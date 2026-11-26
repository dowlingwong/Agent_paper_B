"""Synthetic tests for the ETP HTCondor adapter: no condor_* binary, no pool, no real job."""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "htcondor"))
import htc_events as ev  # noqa: E402
import htc_submit as hs  # noqa: E402
import htc_units as hu  # noqa: E402

CONFIG = hs.load_config()


def manifest(**over):
    m = {"schema": "htc_job/v1", "name": "p1", "kind": "probe", "image": "cverstege/alma9-gridjob",
         "cpus": 1, "memory_mb": 2048, "disk_kb": 1000000, "walltime_s": 1800, "gpus": 0,
         "gpu_device_name": None, "placement": "local", "executable": "/bin/sh", "executable_in_image": True,
         "arguments": ["--out", "a b", "it's"], "transfer_input_files": [], "transfer_output_files": []}
    m.update(over)
    return m


def gpu(**over):
    return manifest(gpus=1, gpu_device_name="NVIDIA A100-PCIE-40GB", placement="remote", **over)


# ----------------------------------------------------------------- config

def test_shipped_config_is_off_and_every_value_has_a_status():
    assert CONFIG["values"]["real_submission_enabled"] is False
    assert all(s.startswith(("ruled:", "measured:", "proposed:")) for s in CONFIG["statuses"].values())
    assert "gpu_device_names" in CONFIG["proposed"]          # wiki facts are not measured yet


def test_config_without_status_is_refused(tmp_path):
    raw = json.loads(hs.DEFAULT_CONFIG.read_text())
    raw["max_gpus"] = {"value": 8}
    p = tmp_path / "c.json"; p.write_text(json.dumps(raw))
    with pytest.raises(hs.HtcError, match="max_gpus"):
        hs.load_config(p)


def test_measured_status_is_accepted(tmp_path):
    raw = json.loads(hs.DEFAULT_CONFIG.read_text())
    raw["max_gpus"]["status"] = "measured: POOL_FACTS.md"
    p = tmp_path / "c.json"; p.write_text(json.dumps(raw))
    assert "max_gpus" not in hs.load_config(p)["proposed"]


# ----------------------------------------------------------------- JDL rendering

def test_local_cpu_jdl():
    m = manifest()
    hs.validate_manifest(m, CONFIG)
    jdl = hs.render_jdl(m, "d" * 64)
    assert "universe = docker\ndocker_image = cverstege/alma9-gridjob\n" in jdl
    assert "requirements = (TARGET.ProvidesETPResources)\n" in jdl
    assert "request_cpus = 1\nrequest_memory = 2048\nrequest_disk = 1000000\n+RequestWalltime = 1800\n" in jdl
    assert "RemoteJob" not in jdl and "request_GPUs" not in jdl and "accounting_group" not in jdl
    assert '''arguments = "--out 'a b' 'it''s'"''' in jdl
    assert jdl.endswith("queue 1\n") and jdl.startswith("# manifest_sha256 = " + "d" * 64)
    assert "transfer_executable = False\n" in jdl and "when_to_transfer_output = ON_EXIT\n" in jdl


def test_gpu_jdl_is_remote_with_exact_device_and_whole_gpus():
    m = gpu(cloud_site="BwForCluster-Nemo2")
    m["gpu_device_name"] = "NVIDIA L40S"
    hs.validate_manifest(m, CONFIG)
    jdl = hs.render_jdl(m, "e" * 64)
    assert "request_GPUs = 1\n+RemoteJob = True\n" in jdl
    assert 'requirements = (TARGET.GPUs_DeviceName =?= "NVIDIA L40S") && (TARGET.CloudSite =?= "BwForCluster-Nemo2")' in jdl
    assert "ProvidesETPResources" not in jdl and "GPUMemory" not in jdl


def test_etp_ceph_and_accounting_group():
    m = gpu(etp_ceph=True, accounting_group="cms.higgs")
    hs.validate_manifest(m, CONFIG)
    jdl = hs.render_jdl(m, "f" * 64)
    assert "(TARGET.ProvidesEtpCeph =?= True)" in jdl and "accounting_group = cms.higgs\n" in jdl


def test_condor_argument_quoting_known_answers():
    assert hs.condor_arguments(["a", "b"]) == '"a b"'
    assert hs.condor_arguments(["one two"]) == "\"'one two'\""
    assert hs.condor_arguments(["x'y"]) == "\"'x''y'\""
    assert hs.condor_arguments(['say "hi"']) == "\"'say \"\"hi\"\"'\""


# ----------------------------------------------------------------- guards

@pytest.mark.parametrize("over, match", [
    ({"gpu_memory_mb": 1000}, "RequestGPUMemoryMB"),
    ({"RequestGPUMemoryMB": 1000}, "RequestGPUMemoryMB"),
    ({"gpus": 1, "gpu_device_name": "NVIDIA A100-PCIE-40GB"}, "placement remote"),
    ({"gpus": 1, "placement": "remote", "gpu_device_name": None}, "exact GPUs_DeviceName"),
    ({"gpus": 1, "placement": "remote", "gpu_device_name": "NVIDIA A100"}, "exact GPUs_DeviceName"),
    ({"gpu_device_name": "NVIDIA L40S"}, "must be null"),
    ({"gpus": 9, "placement": "remote", "gpu_device_name": "NVIDIA L40S"}, "invalid gpus"),
    ({"cloud_site": "BwForCluster-Nemo2"}, "remote jobs only"),
    ({"etp_ceph": True}, "remote jobs only"),
    ({"accounting_group": "nobody"}, "accounting_group"),
    ({"walltime_s": 10 ** 7}, "invalid walltime_s"),
    ({"image": "Bad Image"}, "image"),
    ({"name": "a b"}, "invalid name"),
    ({"arguments": ["ok", "line\nbreak"]}, "single-line"),
    ({"transfer_output_files": ["a,b"]}, "characters outside"),
    ({"surprise": 1}, "unknown"),
    ({"kind": "evidence"}, "kind"),
    ({"arguments": ["$(Cluster)"]}, "macros"),
    ({"arguments": ["a\x0bb"]}, "control characters"),
    ({"name": ".."}, "invalid name"),
    ({"resume_dir": "/abs"}, "resume_dir"),
    ({"resume_dir": "../up"}, "resume_dir"),
])
def test_refusals(over, match):
    with pytest.raises(hs.HtcError, match=match):
        hs.validate_manifest(manifest(**over), CONFIG)


def test_remote_never_requires_etp_resources_even_if_forced():
    m = gpu()
    hs.validate_manifest(m, CONFIG)
    m2 = copy.deepcopy(m); m2["placement"] = "remote"
    jdl = hs.render_jdl(m2, "0" * 64)
    assert "ProvidesETPResources" not in jdl


def test_transfer_input_over_100_mb_is_refused(tmp_path):
    big = tmp_path / "big.bin"
    with open(big, "wb") as fh:
        fh.truncate(100 * 1000 * 1000 + 1)
    with pytest.raises(hs.HtcError, match="over 100 MB"):
        hs.validate_manifest(manifest(transfer_input_files=["big.bin"]), CONFIG, base_dir=tmp_path)
    small = tmp_path / "s.txt"; small.write_text("x")
    assert hs.validate_manifest(manifest(transfer_input_files=["s.txt"]), CONFIG, base_dir=tmp_path)["total_input_bytes"] == 1


def test_missing_or_symlinked_transfer_input_is_refused(tmp_path):
    with pytest.raises(hs.HtcError, match="not a regular file"):
        hs.validate_manifest(manifest(transfer_input_files=["nope.txt"]), CONFIG, base_dir=tmp_path)
    (tmp_path / "t.txt").write_text("x"); os.symlink(tmp_path / "t.txt", tmp_path / "l.txt")
    with pytest.raises(hs.HtcError, match="not a regular file"):
        hs.validate_manifest(manifest(transfer_input_files=["l.txt"]), CONFIG, base_dir=tmp_path)


def test_executable_is_counted_unless_it_lives_in_the_image(tmp_path):
    exe = tmp_path / "probe.sh"
    with open(exe, "wb") as fh:
        fh.truncate(100 * 1000 * 1000)
    small = tmp_path / "s.txt"; small.write_text("x")
    m = manifest(executable="probe.sh", transfer_input_files=["s.txt"]); m.pop("executable_in_image")
    with pytest.raises(hs.HtcError, match="over 100 MB"):
        hs.validate_manifest(m, CONFIG, base_dir=tmp_path)
    m2 = manifest(executable="missing.sh"); m2.pop("executable_in_image")
    with pytest.raises(hs.HtcError, match="executable"):
        hs.validate_manifest(m2, CONFIG, base_dir=tmp_path)


def test_resume_dir_must_exist_and_counts_toward_the_limit(tmp_path):
    with pytest.raises(hs.HtcError, match="existing directory"):
        hs.validate_manifest(manifest(resume_dir="units"), CONFIG, base_dir=tmp_path)
    with pytest.raises(hs.HtcError, match="'.' or '..'"):
        hs.validate_manifest(manifest(resume_dir="."), CONFIG, base_dir=tmp_path)
    (tmp_path / "units").mkdir()
    with open(tmp_path / "units" / "big.bin", "wb") as fh:
        fh.truncate(100 * 1000 * 1000 + 1)
    with pytest.raises(hs.HtcError, match="over 100 MB"):
        hs.validate_manifest(manifest(resume_dir="units"), CONFIG, base_dir=tmp_path)
    (tmp_path / "u2").mkdir(); (tmp_path / "u2" / "l").symlink_to(tmp_path / "units" / "big.bin")
    with pytest.raises(hs.HtcError, match="symlink"):
        hs.validate_manifest(manifest(resume_dir="u2"), CONFIG, base_dir=tmp_path)


def test_resume_dir_survives_eviction(tmp_path):
    (tmp_path / "units").mkdir()
    m = manifest(resume_dir="units", transfer_output_files=["out.json"])
    hs.validate_manifest(m, CONFIG, base_dir=tmp_path)
    jdl = hs.render_jdl(m, "1" * 64)
    assert "when_to_transfer_output = ON_EXIT_OR_EVICT\n" in jdl
    assert "transfer_input_files = units\n" in jdl and "transfer_output_files = out.json,units\n" in jdl


def test_track_g_needs_table_and_runner_timeout_below_walltime():
    base = dict(kind="track_g", table_id="t0_digits", runner_timeout_s=1200, runs_per_job=1)
    hs.validate_manifest(gpu(**base, walltime_s=1801), CONFIG)
    with pytest.raises(hs.HtcError, match="runner timeout plus the margin"):
        hs.validate_manifest(gpu(**base, walltime_s=1800), CONFIG)
    three = dict(base, runs_per_job=3)
    with pytest.raises(hs.HtcError, match="runs_per_job"):
        hs.validate_manifest(gpu(**three, walltime_s=4000), CONFIG)
    hs.validate_manifest(gpu(**three, walltime_s=4201), CONFIG)
    with pytest.raises(hs.HtcError, match="missing"):
        hs.validate_manifest(gpu(kind="track_g", walltime_s=3600), CONFIG)
    bad = gpu(**base, walltime_s=3600); bad["gpu_device_name"] = None
    with pytest.raises(hs.HtcError, match="exact GPUs_DeviceName"):          # CUDA OOM needs a pinned model
        hs.validate_manifest(bad, CONFIG)


def test_table_pins_keep_one_device_per_table(tmp_path):
    pins = tmp_path / "pins.json"
    a = gpu(kind="track_g", table_id="t1", runner_timeout_s=100, runs_per_job=1, walltime_s=3600)
    b = copy.deepcopy(a); b["gpu_device_name"] = "NVIDIA L40S"
    assert hs.check_table_pin(pins, a) == {"t1": "NVIDIA A100-PCIE-40GB"}
    assert hs.check_table_pin(pins, a) == {"t1": "NVIDIA A100-PCIE-40GB"}
    with pytest.raises(hs.HtcError, match="pinned"):
        hs.check_table_pin(pins, b)


def test_probe_manifest_must_not_carry_track_g_keys():
    with pytest.raises(hs.HtcError, match="unknown"):
        hs.validate_manifest(manifest(table_id="x", runner_timeout_s=1), CONFIG)


# ----------------------------------------------------------------- CLI

def test_cli_dry_run_renders_without_condor(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))                     # no condor_submit on PATH
    p = tmp_path / "m.json"; p.write_text(json.dumps(manifest()))
    out = subprocess.run([sys.executable, str(hs.HERE / "htc_submit.py"), str(p), "--dry-run"],
                         capture_output=True, text=True, env={"PATH": str(tmp_path)})
    assert out.returncode == 0, out.stderr
    assert "condor_submit not on PATH" in out.stdout and (tmp_path / "p1.jdl").exists()


def test_cli_dry_run_calls_condor_submit_dry_run_in_the_manifest_directory(tmp_path):
    bindir = tmp_path / "bin"; bindir.mkdir()
    fake = bindir / "condor_submit"
    fake.write_text("#!/bin/sh\necho \"$@\" > \"$(dirname \"$0\")/called.txt\"\npwd >> \"$(dirname \"$0\")/called.txt\"\n")
    fake.chmod(0o755)
    mdir = tmp_path / "jobs"; mdir.mkdir(); outdir = tmp_path / "rendered"
    p = mdir / "m.json"; p.write_text(json.dumps(manifest()))
    out = subprocess.run([sys.executable, str(hs.HERE / "htc_submit.py"), str(p), "--dry-run", "--out", str(outdir)],
                         capture_output=True, text=True, env={"PATH": f"{bindir}:/usr/bin:/bin"}, cwd=str(tmp_path))
    assert out.returncode == 0, out.stderr
    args, cwd = (bindir / "called.txt").read_text().splitlines()
    args = args.split()
    assert args[0] == "-dry-run" and args[-1] == str((outdir / "p1.jdl").resolve()) and cwd == str(mdir.resolve())


def test_cli_track_g_needs_table_pins(tmp_path):
    m = gpu(kind="track_g", table_id="t1", runner_timeout_s=100, runs_per_job=1, walltime_s=3600)
    p = tmp_path / "m.json"; p.write_text(json.dumps(m))
    out = subprocess.run([sys.executable, str(hs.HERE / "htc_submit.py"), str(p), "--dry-run"],
                         capture_output=True, text=True, env={"PATH": str(tmp_path)})
    assert out.returncode == 2 and "--table-pins" in out.stderr


def test_cli_submit_refused_while_disabled(tmp_path):
    p = tmp_path / "m.json"; p.write_text(json.dumps(manifest()))
    out = subprocess.run([sys.executable, str(hs.HERE / "htc_submit.py"), str(p), "--submit"],
                         capture_output=True, text=True)
    assert out.returncode == 2 and "real submission disabled" in out.stderr and not (tmp_path / "p1.jdl").exists()


# ----------------------------------------------------------------- event log

LOG = """000 (123.000.000) 2026-11-14 01:00:00 Job submitted from host: <10.0.0.1:9618>
...
001 (123.000.000) 2026-11-14 01:05:30 Job executing on host: <10.0.0.2:9618>
...
004 (123.000.000) 2026-11-14 01:20:00 Job was evicted.
	(0) CPU times
...
001 (123.000.000) 2026-11-14 01:30:00 Job executing on host: <10.0.0.3:9618>
...
005 (123.000.000) 2026-11-14 01:40:10 Job terminated.
	(1) Normal termination (return value 0)
...
000 (124.000.000) 2026-11-14 01:00:05 Job submitted from host: <10.0.0.1:9618>
...
012 (124.000.000) 2026-11-14 02:00:00 Job was held.
	Job has gone over memory limit of 2048 megabytes. Peak usage: 4096 megabytes.
	Code 34 Subcode 0
...
000 (125.000.000) 2026-11-14 01:00:06 Job submitted from host: <10.0.0.1:9618>
...
001 (125.000.000) 2026-11-14 03:00:00 Job executing on host: <10.0.0.4:9618>
...
005 (125.000.000) 2026-11-14 03:00:09 Job terminated.
	(0) Abnormal termination (signal 9)
...
000 (126.000.000) 2026-11-14 01:00:07 Job submitted from host: <10.0.0.1:9618>
...
"""


def test_queue_rows_from_a_synthetic_log(tmp_path):
    events = ev.parse_events(LOG)
    rows = ev.queue_rows(events, {"123.0": "P1", "124.0": "P2"}, {"123.0": {"site": "TOpAS", "host": "c1", "gpu_name": ""}})
    r = {x["cluster.proc"]: x for x in rows}
    assert r["123.0"]["wait_s"] == 330 and r["123.0"]["run_s"] == 610             # 01:40:10 - last 001 (01:30:00)
    assert r["123.0"]["evictions"] == 1 and r["123.0"]["exit"] == "0" and r["123.0"]["site"] == "TOpAS"
    assert r["123.0"]["submit_utc"] == "2026-11-14T01:00:00Z" and r["123.0"]["end_utc"] == "2026-11-14T01:40:10Z"
    assert r["124.0"]["exit"] == "held" and r["124.0"]["holds"] == 1 and r["124.0"]["wait_s"] == ""
    assert r["125.0"]["exit"] == "signal 9" and r["125.0"]["run_s"] == 9
    assert r["126.0"]["exit"] == "idle" and r["126.0"]["probe"] == ""
    ev.write_tsv(rows, tmp_path / "q.tsv")
    lines = (tmp_path / "q.tsv").read_text().splitlines()
    assert lines[0].split("\t") == list(ev.COLUMNS) and len(lines) == 5


def test_old_date_format_needs_a_year_and_offsets_apply():
    old = "000 (7.000.000) 11/14 02:00:00 Job submitted from host: <h>\n...\n001 (7.000.000) 11/14 02:00:10 Job executing on host: <h>\n...\n"
    with pytest.raises(ev.EventLogError, match="year"):
        ev.parse_events(old)
    e = ev.parse_events(old, year=2026, utc_offset_minutes=60)
    assert e[0]["time"].isoformat() == "2026-11-14T01:00:00+00:00"


def test_truncated_or_garbled_logs_are_refused():
    with pytest.raises(ev.EventLogError, match="truncated"):
        ev.parse_events("000 (1.000.000) 2026-11-14 01:00:00 Job submitted\n")
    with pytest.raises(ev.EventLogError, match="outside an event"):
        ev.parse_events("garbage\n")


@pytest.mark.parametrize("reason, cls", [
    ("Job has gone over memory limit of 2048 megabytes. Code 34 Subcode 0", "htcondor_memory_hold"),
    ("out of resources. Code 34 Subcode 102", "htcondor_memory_hold"),
    ("exceeded its allocated disk. Code 34 Subcode 104", "htcondor_disk_hold"),
    ("out of resources. Code 34 Subcode 104", "htcondor_disk_hold"),
    ("(errno 122) Disk quota exceeded", "unclassified"),
    ("via condor_hold: disk limit test", "unclassified"),
    ("Error writing to disk: file size limit exceeded", "unclassified"),
    ("disk I/O error; retry limit reached. Code 26 Subcode 0", "unclassified"),
    ("Job went over disk quota", "unclassified"),
    ("DiskUsage > RequestDisk. Code 3 Subcode 0", "unclassified"),
    ("Job used 3 GB memory above request; disk limit 10 GB. Code 26 Subcode 0", "unclassified"),
    ("periodic hold: walltime 3600 exceeded; disk 2 GB. Code 26 Subcode 0", "htcondor_walltime_hold"),
    ("Job has gone over memory limit; disk ok. Code 34 Subcode 0", "htcondor_memory_hold"),
    ("invalid image. Code 35 Subcode 0", "htcondor_image_pull"),
    ("duration exceeded. Code 46 Subcode 0", "htcondor_walltime_hold"),
    ("execute time exceeded. Code 47 Subcode 0", "htcondor_walltime_hold"),
    ("periodic hold: walltime 3600 exceeded; MemoryUsage 100. Code 3 Subcode 0", "htcondor_walltime_hold"),
    ("Error response from daemon: could not select device driver with capabilities: [[gpu]]", "unclassified"),
    ("something else. Code 12 Subcode 2", "unclassified"),
    ("Error from slot1@ep: Job has gone over cgroup memory limit of 20096 megabytes", "htcondor_memory_hold"),
    ("Memory usage exceeded the request", "htcondor_memory_hold"),
    ("Job exceeded its requested walltime of 3600 s", "htcondor_walltime_hold"),
    ("Error: Cannot pull docker image r1-htc:20261114: manifest unknown", "htcondor_image_pull"),
    ("Job has been started 6 times", "htcondor_restart_limit"),
    ("via condor_hold (by user dwong)", "unclassified"),
])
def test_hold_classification(reason, cls):
    assert ev.classify_hold(reason) == cls


def test_infrastructure_outcomes_never_reuse_the_runner_timeout_reason():
    events = ev.parse_events(LOG)
    held = ev.infrastructure_outcome(ev.job_summary(events, "124.0"))
    assert held["final"]["kind"] == "infrastructure_failure" and held["final"]["reason"] == "htcondor_memory_hold"
    # 123.0 was evicted, restarted and ended normally: the run's own outcome decides; the eviction is history
    done = ev.infrastructure_outcome(ev.job_summary(events, "123.0"))
    assert done["final"] is None and [a["reason"] for a in done["attempts"]] == ["htcondor_eviction"]
    assert ev.infrastructure_outcome(ev.job_summary(events, "125.0"))["final"] is None  # the runner classifies signals
    reasons = {"htcondor_memory_hold", "htcondor_walltime_hold", "htcondor_image_pull", "htcondor_restart_limit",
               "htcondor_eviction", "htcondor_preemption"}
    assert "timeout" not in reasons


def test_unrecognised_hold_is_unclassified_not_infrastructure():
    log = "000 (9.000.000) 2026-11-14 01:00:00 x\n...\n012 (9.000.000) 2026-11-14 01:01:00 Job was held.\n\tvia condor_hold (by user dwong)\n...\n"
    out = ev.infrastructure_outcome(ev.job_summary(ev.parse_events(log), "9.0"))
    assert out["final"]["kind"] == "unclassified"
    # a recognised hold, a release, then an unrecognised hold: unclassified wins and every hold is listed
    log2 = ("000 (9.000.000) 2026-11-14 01:00:00 x\n...\n012 (9.000.000) 2026-11-14 01:01:00 Job was held.\n"
            "\tJob has gone over memory limit. Code 34 Subcode 102\n...\n013 (9.000.000) 2026-11-14 01:02:00 released\n...\n"
            "012 (9.000.000) 2026-11-14 01:03:00 Job was held.\n\tvia condor_hold (by user dwong)\n...\n")
    out2 = ev.infrastructure_outcome(ev.job_summary(ev.parse_events(log2), "9.0"))
    assert out2["final"]["kind"] == "unclassified" and len(out2["final"]["detail"]) == 2


def test_preemption_wording_maps_to_preemption():
    log = "000 (8.000.000) 2026-11-14 01:00:00 x\n...\n001 (8.000.000) 2026-11-14 01:01:00 x\n...\n004 (8.000.000) 2026-11-14 01:02:00 Job was evicted.\n\tJob was preempted by a higher-priority job\n...\n"
    s = ev.job_summary(ev.parse_events(log), "8.0")
    assert ev.infrastructure_outcome(s)["final"]["reason"] == "htcondor_preemption"
    assert s["exit"] == "idle"                                  # after an eviction the job is idle again


def test_time_zone_suffix_is_applied_once_and_merged_events_are_refused():
    z = ev.parse_events("000 (1.000.000) 2026-11-14 01:00:00+01:00 x\n...\n")
    assert z[0]["time"].isoformat() == "2026-11-14T00:00:00+00:00"
    assert ev.parse_events("000 (1.000.000) 2026-11-14 01:00:00Z x\n...\n")[0]["time"].hour == 1
    with pytest.raises(ev.EventLogError, match="suffix"):
        ev.parse_events("000 (1.000.000) 2026-11-14 01:00:00Z x\n...\n", utc_offset_minutes=60)
    with pytest.raises(ev.EventLogError, match="missing"):
        ev.parse_events("000 (1.000.000) 2026-11-14 01:00:00 x\n001 (1.000.000) 2026-11-14 01:01:00 y\n...\n")


# ----------------------------------------------------------------- resume-safe units

def test_units_skip_completed_after_a_restart(tmp_path):
    calls = []

    def work(unit, d):
        calls.append(unit)
        (d / "out.txt").write_text(unit)
        return ["out.txt"]

    first = hu.run_units(tmp_path, ["u1", "u2"], work)
    assert first["ran"] == ["u1", "u2"]
    second = hu.run_units(tmp_path, ["u1", "u2", "u3"], work)
    assert second["skipped_complete"] == ["u1", "u2"] and second["ran"] == ["u3"]
    assert calls == ["u1", "u2", "u3"]


def test_eviction_mid_unit_leaves_no_manifest_and_partial_output_is_set_aside(tmp_path):
    def crash(unit, d):
        (d / "partial.txt").write_text("half")
        raise KeyboardInterrupt  # stands in for an eviction mid-unit

    with pytest.raises(KeyboardInterrupt):
        hu.run_units(tmp_path, ["u1"], crash)
    assert not (tmp_path / "u1" / hu.MANIFEST).exists()

    def ok(unit, d):
        (d / "out.txt").write_text("full")
        return ["out.txt"]

    res = hu.run_units(tmp_path, ["u1"], ok)
    assert res["ran"] == ["u1"] and "u1" in res["set_aside"]
    assert (Path(res["set_aside"]["u1"]) / "partial.txt").read_text() == "half"     # moved, not deleted


def test_tampered_output_is_a_stop_not_a_silent_redo(tmp_path):
    def work(unit, d):
        (d / "out.txt").write_text("x")
        return ["out.txt"]

    hu.run_units(tmp_path, ["u1"], work)
    (tmp_path / "u1" / "out.txt").write_text("y")
    with pytest.raises(hu.UnitError, match="differs"):
        hu.run_units(tmp_path, ["u1"], work)


def test_mark_complete_requires_real_outputs(tmp_path):
    (tmp_path / "u").mkdir()
    with pytest.raises(hu.UnitError, match="not a regular file"):
        hu.mark_complete(tmp_path / "u", ["missing.txt"])
    with pytest.raises(hu.UnitError, match="invalid unit name"):
        hu.run_units(tmp_path, ["../x"], lambda u, d: [])


def test_disk_hold_is_an_infrastructure_failure_and_walltime_is_not_a_timeout():
    """Author 14 Nov: HTC-Q2 (b) a disk hold is infrastructure_failure/htcondor_disk_hold; HTC-Q1 (a) a walltime hold is
    infrastructure_failure/htcondor_walltime_hold and never the runner's 'timeout' reason (the repeated-timeout cap
    counts only 'timeout')."""
    for text, reason in (("exceeded its allocated disk. Code 34 Subcode 104", "htcondor_disk_hold"),
                         ("duration exceeded. Code 46 Subcode 0", "htcondor_walltime_hold")):
        log = ("000 (7.000.000) 2026-11-14 01:00:00 x\n...\n012 (7.000.000) 2026-11-14 01:01:00 Job was held.\n"
               f"\t{text}\n...\n")
        out = ev.infrastructure_outcome(ev.job_summary(ev.parse_events(log), "7.0"))
        assert out["final"]["kind"] == "infrastructure_failure" and out["final"]["reason"] == reason
        assert text in out["final"]["detail"]
        assert out["final"]["reason"] != "timeout"
