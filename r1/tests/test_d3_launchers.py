"""Tests for the D.3 G1 launchers (design revision 6b) — synthetic, CPU only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from r1.c3.d3 import launch as L
from r1.c3.d3 import launch_htcondor as H
from r1.c3.d3 import launch_ssh as S
from r1.c3.d3 import probe as P
from r1.c3.d3.campaign_chunk import ChunkSpec, check_hardware, sha256_json
from r1.c3.d3.evidence_accounting import AccountingStop, CampaignAccounting, LOSS_SCHEMA, RETRY_SCHEMA

SOURCE = {"path": "docs/r1/authorizations/example.md",
          "sha256": "a" * 64, "model": "NVIDIA RTX 4090"}
UUID = "GPU-cadcadca-1000-2000-3000-400000000000"


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


def _deployment(record):
    model = "NVIDIA RTX 4090"
    chunk = {key: record[key] for key in ("stage", "node", "arm", "repetition", "instance_seeds")}
    chunk.update(manifest_sha256=record["manifest"]["sha256"], gpu_model=model)
    attempt = {"attempt_id": "attempt-1", "state": "infrastructure_lost", "job_id": "760000.0"}
    receipt = json.dumps({**attempt, "schema": LOSS_SCHEMA, "run_id": "d3a-fixture", "chunk": chunk,
                          "job_record_sha256": "d" * 64})
    attempt.update(receipt=receipt, receipt_sha256=hashlib.sha256(receipt.encode()).hexdigest())
    ledger = {"schema": RETRY_SCHEMA, "run_id": "d3a-fixture", "chunk": chunk,
              "attempts": [attempt, {"attempt_id": "attempt-2", "state": "current"}]}
    return {**record, "observed": {"path": "observed.json", "probe": True}, "retry_ledger": ledger,
            "hardware": {**record["hardware"], "proposer_gpu_uuid": UUID}}


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


@pytest.mark.parametrize("changed", ["missing", "arm", "seeds", "manifest", "retry_gpu", "receipt",
                                     "attempt_id", "attempt_state", "duplicate_job", "foreign_loss"])
def test_deployment_refuses_invalid_retry_ledger(changed):
    record = _deployment(_record())
    ledger = record["retry_ledger"]
    prior, current = ledger["attempts"]
    if changed == "missing":
        del record["retry_ledger"]
    elif changed == "arm":
        ledger["chunk"]["arm"] = "A0"
    elif changed == "seeds":
        ledger["chunk"]["instance_seeds"] = [6201]
    elif changed == "manifest":
        ledger["chunk"]["manifest_sha256"] = "0" * 64
    elif changed == "retry_gpu":
        ledger["chunk"]["gpu_model"] = "NVIDIA L40S"
    elif changed == "receipt":
        prior["receipt_sha256"] = "unsealed"
    elif changed == "attempt_id":
        current["attempt_id"] = prior["attempt_id"]
    elif changed == "attempt_state":
        prior["state"] = "success"
    elif changed == "foreign_loss":
        prior["job_id"] = "760007.0"
    else:
        ledger["attempts"].insert(1, {**prior, "attempt_id": "different"})
    with pytest.raises(L.LaunchStop, match="retry ledger|prior attempt"):
        L.validate_deployment_launch(record)


def test_deployment_checks_the_live_reservation():
    record = _deployment(_record(lease_path="/lease/gpu0.lock"))
    observed = {"schema": L.OBSERVED_SCHEMA, "model": "NVIDIA RTX 4090", "gpu_uuid": UUID,
                "lease": True, "lease_kind": "lease", "lease_path": "/lease/gpu0.lock"}
    accounting = CampaignAccounting.from_job(record, observed)
    assert accounting.infra_attempts == 2
    with pytest.raises(AccountingStop, match="positive elapsed"):
        accounting.receipt(100, 100)
    for change in [{"lease": False}, {"lease_kind": "htcondor"}, {"lease_path": "/lease/gpu1.lock"},
                   {"gpu_uuid": ""}, {"gpu_uuid": "GPU-another"}, {"model": "NVIDIA L40S"}]:
        with pytest.raises(AccountingStop, match="reservation"):
            CampaignAccounting.from_job(record, observed | change)


def test_deployment_condor_probes_the_cuda_assignment(monkeypatch):
    record = _deployment(_record(launcher="htcondor"))
    monkeypatch.setattr(P, "assigned_cuda_uuid", lambda: UUID)

    def runner(argv, **kwargs):
        if "--query-gpu=name,uuid,driver_version,memory.total,memory.free" in argv:
            assert argv[1:3] == ["-i", UUID]
            return SimpleNamespace(returncode=0, stdout=f"NVIDIA RTX 4090, {UUID}, 535, 24564, 24000\n")
        return SimpleNamespace(returncode=0, stdout="")

    manifest = {"proposer_model": "gemma4_31b"}
    observed = P.probe_from_records(record, manifest, runner=runner)
    assert CampaignAccounting.from_job(record, observed).gpu_uuid == UUID
    with pytest.raises(L.LaunchStop, match="without an index override"):
        P.probe_from_records(record, manifest, gpu_index=0, runner=runner)


def test_assigned_cuda_uuid_reads_the_single_visible_device(monkeypatch):
    import ctypes
    from uuid import UUID as ParseUUID

    def count(target):
        target._obj.value = 1
        return 0

    def get_uuid(target, device):
        target.raw = ParseUUID(UUID[4:]).bytes
        return 0

    driver = SimpleNamespace(cuInit=lambda _: 0, cuDeviceGetCount=count,
                             cuDeviceGet=lambda _, ordinal: ordinal, cuDeviceGetUuid=get_uuid)
    monkeypatch.setattr(ctypes, "CDLL", lambda name: driver)
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "2")
    assert P.assigned_cuda_uuid() == UUID
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "2,3")
    with pytest.raises(L.LaunchStop, match="one CUDA_VISIBLE_DEVICES"):
        P.assigned_cuda_uuid()


@pytest.mark.parametrize("lease_name,selector", [("gpu3.lock", "3"), (UUID + ".lock", UUID)])
def test_deployment_ssh_probes_the_exact_lease(lease_name, selector):
    lease = "/leases/" + lease_name
    record = _deployment(_record(lease_path=lease))
    manifest = {"proposer_model": "gemma4_31b"}

    def runner(argv, **kwargs):
        if "--query-gpu=name,uuid,driver_version,memory.total,memory.free" not in argv:
            return SimpleNamespace(returncode=0, stdout="")
        assert argv[1:3] == ["-i", selector]
        return SimpleNamespace(returncode=0, stdout=f"NVIDIA RTX 4090, {UUID}, 535, 24564, 24000\n")

    assert P.probe_from_records(record, manifest, lease_path=lease, runner=runner)["gpu_uuid"] == UUID
    with pytest.raises(L.LaunchStop, match="lease paths differ"):
        P.probe_from_records(record, manifest, lease_path="/leases/gpu0.lock", runner=runner)
    wrong = "/leases/GPU-11111111-1111-1111-1111-111111111111.lock"
    with pytest.raises(L.LaunchStop, match="must name the card index or"):
        P.probe_from_records({**record, "lease_path": wrong}, manifest, lease_path=wrong, runner=runner)


def test_deployment_checks_inherited_lease_fd(tmp_path):
    import fcntl

    lease, other = tmp_path / "gpu4.lock", tmp_path / "other.lock"
    other.touch()
    with lease.open("w") as fh:
        P.check_ssh_lease_fd(str(lease), fd=fh.fileno())
        with lease.open("r") as contender, pytest.raises(BlockingIOError):
            fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(L.LaunchStop, match="does not match"):
            P.check_ssh_lease_fd(str(other), fd=fh.fileno())


def test_deployment_launchers_stage_one_fresh_attempt(tmp_path):
    launch_path, manifest, _, _ = _staged(tmp_path)
    record = _deployment(L.read_json(launch_path))
    ledger = record["retry_ledger"]
    prior, current = ledger["attempts"]
    raw_receipt = tmp_path / "loss_receipt.json"
    raw_receipt.write_bytes(prior["receipt"].encode())
    submitted = dict(record)
    submitted["retry_ledger"] = {**ledger, "attempts": [
        {key: value for key, value in prior.items() if key != "receipt"} | {"receipt_path": raw_receipt.name},
        current,
    ]}
    L.write_launch(launch_path, submitted)
    calls = []

    def runner(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout="1 job(s) submitted to cluster 760001.\n", stderr="")

    submit = tmp_path / "submit"
    out = tmp_path / "results" / "out"
    result = H.submit(launch_path, out, submit_dir=submit, manifest_path=manifest, runner=runner)
    assert result["cluster_id"] == "760001"
    assert calls[-1][0][-1] == H.SUBMIT_NAME and calls[-1][1]["cwd"] == submit
    assert L.read_json(submit / "launch.json")["retry_ledger"] == record["retry_ledger"]
    with pytest.raises(L.LaunchStop, match="already exists"):
        H.submit(launch_path, out, submit_dir=submit, manifest_path=manifest, runner=runner)
    assert len(calls) == 1

    result = S.launch(launch_path, out, manifest_path=manifest, lease_path="/leases/gpu0.lock", runner=runner)
    assert result["ssh_rc"] == 0
    command, kwargs = calls[-1]
    assert f"mkdir -- {out.parent}" in command[-1]
    assert "--out out" in kwargs["input"]
    assert L.read_json(out.parent / "launch.json")["retry_ledger"] == record["retry_ledger"]
    with pytest.raises(L.LaunchStop, match="already claimed"):
        S.launch(launch_path, out, manifest_path=manifest, lease_path="/leases/gpu0.lock", runner=runner)
    assert len(calls) == 2
    raw_receipt.write_text("{\"tampered\": true}\n")
    with pytest.raises(L.LaunchStop, match="SHA-256 differs"):
        H.submit(launch_path, out, submit_dir=tmp_path / "different", manifest_path=manifest, runner=runner)
    assert len(calls) == 2


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
