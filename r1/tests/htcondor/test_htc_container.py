"""HTCondor container universe (author, 14 Nov): ``runtime``, ``container_image``, ``container_transfer``.

AI-assisted (Claude); synthetic, no HTCondor needed. The four S2 job files the cluster agent wrote by hand
(``data/s2``) are the references: the adapter's rendering of the matching manifests must be equivalent to them
(same submit commands and values after normalising key case and aliases, argument syntax and the order of the
``requirements`` clauses).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "r1" / "scripts" / "htcondor"))
import htc_events as ev  # noqa: E402
import htc_submit as hs  # noqa: E402

S2 = HERE / "data" / "s2"
ALIASES = {"requestcpus": "request_cpus", "requestmemory": "request_memory", "requestdisk": "request_disk",
           "requestgpus": "request_gpus"}


def jdl_commands(text: str) -> dict:
    """Submit commands as a normalised dict (comments and blank lines dropped)."""
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("queue"):
            out["queue"] = line.split(None, 1)[1] if " " in line else "1"
            continue
        k, v = (s.strip() for s in line.split("=", 1))
        k = ALIASES.get(k.lower(), k.lower())
        if k == "arguments":
            v = v[1:-1].split() if v.startswith('"') and v.endswith('"') else v.split()
        elif k == "requirements":
            v = sorted(re.sub(r"^\((.*)\)$", r"\1", c.strip()) for c in v.split("&&"))
        out[k] = v
    return out


def config(tmp_path=None, **over):
    cfg = hs.load_config()
    for k, val in over.items():
        cfg["values"][k] = val
    return cfg


def s2_manifest(name, *, gpus=0, device=None, placement="local", cloud_site=None, cpus=1, memory=2048):
    m = {"schema": "htc_job/v1", "name": name, "kind": "probe", "runtime": "container",
         "container_image": "docker://cverstege/alma9-gridjob", "cpus": cpus, "memory_mb": memory,
         "disk_kb": 5000000, "walltime_s": 1800, "gpus": gpus, "gpu_device_name": device, "placement": placement,
         "executable": "probe.sh", "arguments": [name], "transfer_input_files": ["probe.sh"],
         "transfer_output_files": []}
    if cloud_site:
        m["cloud_site"] = cloud_site
    return m


S2_CASES = {
    "S2L_local_cpu.jdl": s2_manifest("S2L"),
    "S2N1_nemo2_l40s.jdl": s2_manifest("S2N1", gpus=1, device="NVIDIA L40S", placement="remote",
                                       cloud_site="BwForCluster-Nemo2", cpus=2, memory=4000),
    "S2N2_nemo2_h200.jdl": s2_manifest("S2N2", gpus=1, device="NVIDIA H200", placement="remote",
                                       cloud_site="BwForCluster-Nemo2", cpus=2, memory=4000),
    "S2T_topas_v100s.jdl": s2_manifest("S2T", gpus=1, device="Tesla V100S-PCIE-32GB", placement="remote",
                                       cpus=2, memory=4000),
}


def test_reference_copies_are_unchanged():
    sums = dict(line.split()[::-1] for line in (S2 / "SHA256SUMS").read_text().splitlines())
    assert sorted(sums) == sorted(S2_CASES)
    for name, digest in sums.items():
        assert hashlib.sha256((S2 / name).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("ref", sorted(S2_CASES))
def test_rendering_is_equivalent_to_the_cluster_agents_s2_jdl(tmp_path, ref):
    (tmp_path / "probe.sh").write_text("#!/bin/bash\nexit 0\n")
    m = S2_CASES[ref]
    hs.validate_manifest(m, config(), base_dir=tmp_path)
    got = jdl_commands(hs.render_jdl(m, "0" * 64))
    want = jdl_commands((S2 / ref).read_text())
    assert got == want


def test_docker_runtime_is_unchanged_and_default():
    m = {"schema": "htc_job/v1", "name": "p", "kind": "probe", "image": "alma9:latest", "cpus": 1, "memory_mb": 1,
         "disk_kb": 1, "walltime_s": 60, "gpus": 0, "gpu_device_name": None, "placement": "local",
         "executable": "x.sh", "executable_in_image": True, "arguments": [], "transfer_input_files": [],
         "transfer_output_files": []}
    hs.validate_manifest(m, config())
    text = hs.render_jdl(m, "0" * 64)
    assert "universe = docker\ndocker_image = alma9:latest\n" in text and "container" not in text
    assert hs.render_jdl({**m, "runtime": "docker"}, "0" * 64) == text
    with pytest.raises(hs.HtcError, match="container_transfer applies"):
        hs.validate_manifest({**m, "container_transfer": True}, config())
    with pytest.raises(hs.HtcError, match="unknown \\['container_image'\\]"):
        hs.validate_manifest({**m, "container_image": "docker://x"}, config())


def base_container(**over):
    m = {**s2_manifest("job"), "executable": "run.sh", "executable_in_image": True, "transfer_input_files": []}
    m.update(over)
    return m


def test_sif_on_shared_fs_for_a_local_job_is_not_transferred():
    m = base_container(container_image="/work/dwong/paperb/images/r1.sif")
    out = hs.validate_manifest(m, config())
    assert out["container"] == {"kind": "sif", "transfer": False, "bytes": None, "shared_fs": True}
    text = hs.render_jdl(m, "0" * 64)
    assert "universe = container\ncontainer_image = /work/dwong/paperb/images/r1.sif\ntransfer_container = false\n" in text
    assert "transfer_input_files" not in text            # the SIF never joins the ordinary inputs
    for bad, msg in ((dict(container_image="/tmp/r1.sif"), "shared file system"),
                     (dict(container_image="/work/x/../y.sif"), "absolute path to a .sif"),
                     (dict(container_image="r1.sif"), "absolute path to a .sif"),
                     (dict(container_image="/work/r1.img"), "absolute path to a .sif"),
                     (dict(container_image="/work/r1.sif", container_transfer=True), "for remote jobs"),
                     (dict(container_image="/work/r1.sif", container_transfer="yes"), "boolean"),
                     (dict(container_image="docker://Bad Image"), "docker://")):
        with pytest.raises(hs.HtcError, match=msg):
            hs.validate_manifest(base_container(**bad), config())


def remote(**over):
    return base_container(placement="remote", gpus=1, gpu_device_name="NVIDIA L40S", cloud_site="BwForCluster-Nemo2",
                          **over)


def test_remote_sif_needs_explicit_transfer_and_its_own_cap(tmp_path):
    sif = tmp_path / "r1.sif"
    sif.write_bytes(b"\0" * 3_000_000)
    with pytest.raises(hs.HtcError, match="needs container_transfer: true"):
        hs.validate_manifest(remote(container_image=str(sif)), config())
    with pytest.raises(hs.HtcError, match="needs container_transfer: true"):
        hs.validate_manifest(remote(container_image="/work/dwong/r1.sif", container_transfer=False), config())
    m = remote(container_image=str(sif), container_transfer=True)
    out = hs.validate_manifest(m, config(max_container_transfer_mb=4))
    assert out["container"]["transfer"] is True and out["container"]["bytes"] == 3_000_000
    assert out["total_input_bytes"] == 0                  # not counted toward max_transfer_input_mb
    text = hs.render_jdl(m, "0" * 64)
    assert f"container_image = {sif}\n" in text and "transfer_container" not in text   # HTCondor transfers it
    with pytest.raises(hs.HtcError, match="over max_container_transfer_mb"):
        hs.validate_manifest(m, config(max_container_transfer_mb=2))
    with pytest.raises(hs.HtcError, match="not a regular file"):
        hs.validate_manifest(remote(container_image=str(tmp_path / "missing.sif"), container_transfer=True), config())
    link = tmp_path / "link.sif"
    link.symlink_to(sif)
    with pytest.raises(hs.HtcError, match="not a regular file"):
        hs.validate_manifest(remote(container_image=str(link), container_transfer=True), config())
    with pytest.raises(hs.HtcError, match="smaller than the transferred SIF"):
        hs.validate_manifest({**m, "disk_kb": 2000}, config(max_container_transfer_mb=4))   # 2,048,000 B < 3,000,000 B
    with pytest.raises(hs.HtcError, match="transferred twice"):
        hs.validate_manifest({**m, "transfer_input_files": [str(sif)]}, config(max_container_transfer_mb=4))
    with pytest.raises(hs.HtcError, match="SIF image only"):
        hs.validate_manifest(remote(container_image="docker://cverstege/alma9-gridjob", container_transfer=True),
                             config())


def test_ordinary_inputs_keep_the_100_mb_cap_with_a_transferred_sif(tmp_path):
    sif = tmp_path / "r1.sif"
    sif.write_bytes(b"\0" * 10)
    big = tmp_path / "data.bin"
    with open(big, "wb") as fh:
        fh.truncate(101_000_000)
    m = remote(container_image=str(sif), container_transfer=True, transfer_input_files=["data.bin"])
    with pytest.raises(hs.HtcError, match="over 100 MB"):
        hs.validate_manifest(m, config(), base_dir=tmp_path)


def test_config_carries_a_proposed_container_cap():
    cfg = hs.load_config()
    assert "max_container_transfer_mb" in cfg["proposed"]
    assert "S5" in cfg["statuses"]["max_container_transfer_mb"]


def test_runtime_container_requires_container_image_only():
    m = base_container()
    with pytest.raises(hs.HtcError, match="missing \\['container_image'\\]"):
        hs.validate_manifest({k: v for k, v in m.items() if k != "container_image"}, config())
    with pytest.raises(hs.HtcError, match="unknown \\['image'\\]"):
        hs.validate_manifest({**m, "image": "alma9"}, config())
    with pytest.raises(hs.HtcError, match="runtime must be"):
        hs.validate_manifest({**m, "runtime": "singularity"}, config())


def test_input_transfer_time_is_recorded_from_the_event_log():
    log = ("000 (5.000.000) 2026-11-14 10:00:00 Job submitted from host: <1.2.3.4>\n...\n"
           "040 (5.000.000) 2026-11-14 10:01:00 Started transferring input files\n\tTransferring to host: <x>\n...\n"
           "040 (5.000.000) 2026-11-14 10:03:30 Finished transferring input files\n...\n"
           "001 (5.000.000) 2026-11-14 10:03:31 Job executing on host: <x>\n...\n"
           "004 (5.000.000) 2026-11-14 10:10:00 Job was evicted.\n...\n"
           "040 (5.000.000) 2026-11-14 10:11:00 Started transferring input files\n...\n"
           "040 (5.000.000) 2026-11-14 10:11:20 Finished transferring input files\n...\n"
           "040 (5.000.000) 2026-11-14 10:20:00 Started transferring output files\n...\n"
           "040 (5.000.000) 2026-11-14 10:20:05 Finished transferring output files\n...\n"
           "005 (5.000.000) 2026-11-14 10:20:06 Job terminated.\n\t(1) Normal termination (return value 0)\n...\n")
    s = ev.job_summary(ev.parse_events(log), "5.0")
    assert s["input_transfer_s"] == 150 + 20               # both attempts; output transfer not counted
    rows = ev.queue_rows(ev.parse_events(log), {"5.0": "S5"})
    assert rows[0]["input_transfer_s"] == 170 and "input_transfer_s" in ev.COLUMNS
    unfinished = ("000 (6.000.000) 2026-11-14 10:00:00 x\n...\n"
                  "040 (6.000.000) 2026-11-14 10:01:00 Started transferring input files\n...\n")
    assert ev.job_summary(ev.parse_events(unfinished), "6.0")["input_transfer_s"] == ""
