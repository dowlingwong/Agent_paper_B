"""Tests for the D.3 G1 launchers (design revision 6b) — synthetic, CPU only."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from r1.c3.d3 import launch as L
from r1.c3.d3 import launch_htcondor as H
from r1.c3.d3 import launch_ssh as S
from r1.c3.d3.campaign_chunk import ChunkSpec, sha256_json

SOURCE = {"path": "docs/r1/authorizations/example.md",
          "sha256": "a" * 64, "model": "NVIDIA RTX 4090"}


def _record(**kw):
    base = {
        "schema": L.LAUNCH_SCHEMA, "stage": "a", "arm": "A2", "node": "digits_mlp",
        "repetition": 0, "instance_seeds": list(range(6201, 6219)), "W": 20, "llm_cap": 80,
        "launcher": "ssh", "host": "TASL-2", "campaign_model_source": dict(SOURCE),
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
    assert got == {"count": 2, "used_memory_mib": 1536}
    assert "1234" not in json.dumps(got) and "GPU-" not in json.dumps(got)


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
