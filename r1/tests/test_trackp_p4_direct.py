"""Track P P.4 phase 1 under R1-HOST-FREE: host classes in the spec, the job told its class, the direct launch path
(``p4_direct.py``: a GPU lease, a fresh job directory, the digest-pinned container with only the leased card, the
launcher record), sealing and charging a direct attempt (GPU-hours on any card), the per-class host-config fill, and
rows (g) (R1-NO-TIMEOUT (3) reporting thresholds; R1-CARD-SHARE free memory, other processes, losses beside another
process). Synthetic only: fakes for nvidia-smi, the container runtime and the clock; real ``flock`` on temporary
files; no GPU, no container, no network, no label file. Imports no torch (runs in the desk suite). AI-assisted
(Claude).
"""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "r1" / "scripts" / "htcondor" / "trackp_p4"
sys.path.insert(0, str(PKG))
import p4_direct as D  # noqa: E402
import p4_fill_host_config as FH  # noqa: E402
import p4_lib as L  # noqa: E402
import p4_render_jdl as RJ  # noqa: E402
import p4_switch as SW  # noqa: E402

ADA, H200 = "ada_rtx6000", "nemo2_h200"
SPEC = json.loads((PKG / "p4_spec.json").read_text())
PROBE_TEMPLATE = json.loads((PKG / L.PROBE_SPEC_FILE).read_text())
ADA_NAME = "NVIDIA RTX 6000 Ada Generation"
UUID = "GPU-0a0b0c0d-0000-1111-2222-333344445555"


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _res(rc=0, out="", err=""):
    return subprocess.CompletedProcess([], rc, out, err)


def _ada_values(work_root: str, lock_dir: str, **over) -> dict:
    v = {p: FH.ADA_FIXED.get(p) for p in FH.expected(ADA)}
    v.update({"work_dir": ".", "gpu.lock_path": "gpu0.lock",
              **{f"bases.{b}.local_path": f"models/{b}" for b in FH.UNUSED_BASES},
              "venv.causal_conv1d": "1.7.0 built from source in image v2.2 (R1-TRACKP-IMAGE-V22-B)",
              "direct.container_runtime": "docker", "direct.work_root": work_root, "direct.lock_dir": lock_dir,
              "direct.hostname": "ucrtasl", "direct.shm_size": "16g", "direct.min_free_mib": "40000"})
    v.update(over)
    return {"schema": FH.SCHEMA_V2, "host_class": ADA, "values": v}


@pytest.fixture
def ada_repo(tmp_path):
    """A stand-in checkout whose Ada host config is filled by the fill hook (work root and lease dir in tmp)."""
    repo = tmp_path / "repo"
    (repo / L.ADA_HOST_CONFIG).parent.mkdir(parents=True)
    shutil.copy2(ROOT / L.ADA_HOST_CONFIG, repo / L.ADA_HOST_CONFIG)
    values = tmp_path / "ada_fill.json"
    values.write_text(json.dumps(_ada_values(str(tmp_path / "work"), str(tmp_path / "locks"))))
    out = FH.fill(values, repo / L.ADA_HOST_CONFIG, host_class=ADA)
    return repo, out["sha256"]


def _probe_spec(ada_sha: str) -> dict:
    s = copy.deepcopy(PROBE_TEMPLATE)
    s["paper"]["commit"] = "3" * 40
    s["image"]["versions_sha256"] = "4" * 64
    s["host_class"] = ADA
    s["hosts"][ADA]["host_config"]["sha256"] = ada_sha
    return s


def _launch_spec(ada_sha: str, classes=(ADA,)) -> dict:
    s = copy.deepcopy(SPEC)
    s["paper"]["commit"] = "3" * 40
    s["image"].update(versions_sha256="4" * 64)
    s["hosts"] = {c: s["hosts"][c] for c in classes}
    for c in classes:
        s["hosts"][c]["host_config"]["sha256"] = ada_sha if c == ADA else "5" * 64
        s["hosts"][c]["estimate"]["source"] = f"{L.HOST_CLASSES[c]['probe_label']}: docs/r1/reports/{c}.md"
    s["labels"].update(partition_sha256="6" * 64, receipt_sha256="7" * 64,
                       freeze_record={"path": "docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_20991231.md",
                                      "sha256": "8" * 64})
    s["caps"].update(probe_gpu_hours=0.5, probe_charge_files={"trackp-p4-probe-20261125-a": ["9" * 64]})
    return s


# ============================================================================================ host classes in the spec
def test_the_shipped_specs_admit_both_classes_and_name_no_fixed_gpu_model():
    for s in (SPEC, PROBE_TEMPLATE):
        assert "gpu_model" not in s and "host_config" not in s and "estimate" not in s
        assert set(s["hosts"]) == set(L.HOST_CLASSES) == {H200, ADA}
        for c, h in s["hosts"].items():
            assert {k: h[k] for k in L.HOST_FIXED} == {k: L.HOST_CLASSES[c][k] for k in L.HOST_FIXED}
            assert h["host_config"]["path"] == L.HOST_CLASSES[c]["host_config_path"]
            assert L._placeholder(h["host_config"]["sha256"]) and L._placeholder(h["estimate"]["source"])
    assert L.HOST_CLASSES[ADA] == {"launch": "direct", "gpu_name": ADA_NAME, "compute_capability": "8.9",
                                   "host_config_path": "r1/scripts/configs/trackp_ada_v1.json",
                                   "probe_label": "ada_sft_probe", "smoke_label": "ada_smoke_e0"}
    assert L.HOST_CLASSES[H200]["gpu_name"] == L.GPU_MODEL == "NVIDIA H200"
    assert L._placeholder(PROBE_TEMPLATE["host_class"]) and "host_class" not in SPEC
    assert "R1-HOST-FREE" in L.PLAN_ROWS
    L.validate_spec(copy.deepcopy(SPEC))
    L.validate_spec(copy.deepcopy(PROBE_TEMPLATE))


def test_spec_refuses_the_old_fixed_gpu_model_and_unadmitted_or_altered_classes():
    s = _launch_spec("a" * 64, (ADA, H200))
    assert L.validate_spec(s, launch=True)["run_id"] == SPEC["run_id"]
    for edit, match in (
            (lambda t: t.update(gpu_model="NVIDIA H200"), "gpu_model is replaced"),
            (lambda t: t.update(host_config={"path": L.HOST_CONFIG, "sha256": "5" * 64}), "host_config is per host"),
            (lambda t: t.update(estimate={}), "estimate is per host"),
            (lambda t: t.update(hosts={}), "hosts must admit"),
            (lambda t: t["hosts"].update(tasl2_rtx4090=t["hosts"][ADA]), "hosts must admit"),
            (lambda t: t["hosts"][ADA].update(gpu_name="NVIDIA L40S"), "hosts.ada_rtx6000 must be"),
            (lambda t: t["hosts"][ADA].update(launch="htcondor"), "hosts.ada_rtx6000 must be"),
            (lambda t: t["hosts"][ADA].update(compute_capability="9.0"), "hosts.ada_rtx6000 must be"),
            (lambda t: t["hosts"][ADA]["host_config"].update(path=L.HOST_CONFIG), "host_config.path"),
            (lambda t: t["hosts"][ADA]["host_config"].update(sha256="TODO"), "hosts.ada_rtx6000.host_config.sha256"),
            (lambda t: t["hosts"][ADA].update(extra=1), "holds only"),
            (lambda t: t["hosts"][ADA]["estimate"].update(source="TODO: later"), "ada_sft_probe: docs/r1/reports"),
            (lambda t: t["hosts"][ADA]["estimate"].update(source="h200_sft_probe: docs/r1/reports/x.md"),
             "ada_sft_probe: docs/r1/reports"),
            (lambda t: t["hosts"][H200]["estimate"]["hours"].pop("kev-4b"), "nemo2_h200.estimate.hours"),
            (lambda t: t.update(host_class=ADA), "names none")):
        t = copy.deepcopy(s)
        edit(t)
        with pytest.raises(L.Stop, match=match):
            L.validate_spec(t, launch=True)
    with pytest.raises(L.Stop, match="not admitted"):
        L.host_class_of(_launch_spec("a" * 64, (H200,)), ADA)
    with pytest.raises(L.Stop, match="starts by direct"):
        L.host_class_of(s, ADA, launch="htcondor")


def test_each_arm_is_projected_at_its_slowest_admitted_class_and_the_walltime_bound_is_htcondor_only():
    s = _launch_spec("a" * 64, (ADA, H200))
    s["hosts"][ADA]["estimate"]["hours"]["kev-4b"] = 12.0
    assert L.arm_hours(s, "kev-4b") == 12.0 and L.arm_hours(s, "kev-4b", H200) == 6.64
    assert L.projection(s)["per_arm"]["kev-4b"]["gpu_hours"] == round(12.0 + 0.5, 3)
    s["hosts"][ADA]["estimate"]["hours"]["kev-4b"] = 19.0      # 19 h x 1.5 + 0.5 h > 86,400 s: no HTCondor request here
    assert L.validate_spec(s, launch=True)["run_id"] == SPEC["run_id"]
    s["hosts"][H200]["estimate"]["hours"]["kev-4b"] = 19.0     # an HTCondor job would request it: refused
    with pytest.raises(L.Stop, match="on nemo2_h200, over 86400 s"):
        L.validate_spec(s, launch=True)


def test_rows_g_the_cap_figures_are_reporting_thresholds():
    s = _launch_spec("a" * 64)
    for h in s["hosts"][ADA]["estimate"]["hours"]:
        s["hosts"][ADA]["estimate"]["hours"][h] = 15.0
    got = L.validate_spec(s, launch=True)                     # 4 x 15.5 + 0.5 GPU-h: reported, not refused
    assert got["threshold"]["reached"] == ["gpu_hours", "slot_hours"] and got["threshold"]["report_to_author"]
    assert "R1-NO-TIMEOUT (3)" in got["threshold"]["rule"]
    s["caps"]["probe_gpu_hours"] = 55.0
    assert L.validate_spec(s, launch=True)["threshold"]["gpu_hours"] > 40
    assert L.threshold_report(L.projection(s), 12.0)["reached"] == ["slot_hours"]


# ============================================================================================ the job's identity
def test_gpu_identity_admits_the_jobs_declared_class_only():
    ada = lambda a, **k: _res(0, f"{ADA_NAME}, {UUID}, 550.54, 49140 MiB, 8.9\n")  # noqa: E731
    got = L.gpu_identity(ada, ADA)
    assert got == {"name": ADA_NAME, "uuid": UUID, "driver": "550.54", "memory_total": "49140 MiB",
                   "compute_capability": "8.9", "host_class": ADA}
    with pytest.raises(L.Stop, match="not NVIDIA H200"):
        L.gpu_identity(ada, H200)
    with pytest.raises(L.Stop, match=f"not {ADA_NAME}"):
        L.gpu_identity(lambda a, **k: _res(0, "NVIDIA H200, GPU-1, 570, 143771 MiB, 9.0\n"), ADA)
    with pytest.raises(L.Stop, match="compute capability"):
        L.gpu_identity(lambda a, **k: _res(0, f"{ADA_NAME}, GPU-1, 550, 49140 MiB, 9.0\n"), ADA)
    with pytest.raises(L.Stop, match="nvidia-smi lists 2"):
        L.gpu_identity(lambda a, **k: _res(0, f"{ADA_NAME}, a, b, c, 8.9\n" * 2), ADA)
    with L._job_host(ADA):                                    # the job's class is the default inside the job
        assert L.gpu_identity(ada)["host_class"] == ADA and L.job_host_config() == L.ADA_HOST_CONFIG
    assert L.job_host_class() == H200 and L.job_host_config() == L.HOST_CONFIG
    with pytest.raises(L.Stop, match="unknown host class"):
        L._job_host("tasl2")


def test_a_direct_job_runs_on_its_leased_card_only():
    gpu = {"uuid": UUID}
    assert L.lease_binding(gpu, {L.LEASED_GPU_ENV: UUID}, ADA) == {"leased_uuid": UUID, "env": L.LEASED_GPU_ENV}
    for env in ({}, {L.LEASED_GPU_ENV: "GPU-other"}):
        with pytest.raises(L.Stop, match="leased card only"):
            L.lease_binding(gpu, env, ADA)
    assert L.lease_binding(gpu, {}, H200) is None


def test_rows_g_card_processes_are_recorded_and_an_oom_beside_another_is_infrastructure():
    out = f"{UUID}, 111, 2000\n{UUID}, 222, 500\nGPU-other, 333, 9000\n"
    assert L.card_processes(lambda a, **k: _res(0, out), UUID) == {"count": 2, "memory_mib": 2500.0}
    assert "error" in L.card_processes(lambda a, **k: _res(9, "", "no driver"), UUID)

    def boom(a, **k):
        raise FileNotFoundError("nvidia-smi")
    assert "FileNotFoundError" in L.card_processes(boom, UUID)["error"]
    rec = {"stop": "STOP: CUDA OOM in sft-dev", "stop_class": "arm", "card_processes_start": {"count": 0},
           "card_processes_end": {"count": 1, "memory_mib": 9000.0}}
    assert L.shared_card_loss(rec) and rec["stop_class"] == "infrastructure" and rec["lost_beside_another_process"]
    alone = {"stop": "STOP: CUDA OOM", "stop_class": "arm", "card_processes_start": {"count": 0}}
    assert not L.shared_card_loss(alone) and alone["stop_class"] == "arm"                 # the author's STOP (P4-MB)
    host_side = {"stop": "STOP: CUDA OOM", "stop_class": "arm"}
    assert L.shared_card_loss(host_side, {"count": 3, "memory_mib": 1.0}, None)
    other = {"stop": "STOP: x", "stop_class": "protocol", "card_processes_start": {"count": 2}}
    assert not L.shared_card_loss(other) and other["stop_class"] == "protocol"


# ============================================================================================ the direct stage
def test_the_direct_descriptor_is_canonical_and_needs_a_filled_host_config(ada_repo):
    repo, sha = ada_repo
    ps = _probe_spec(sha)
    text = RJ.render_direct(ps, "kev-0.8b", ADA, mode="probe", repo=repo)
    assert text == RJ.render_direct(ps, "kev-0.8b", ADA, mode="probe", repo=repo)        # deterministic
    d = json.loads(text)
    assert d["schema"] == D.DESCRIPTOR_SCHEMA and d["preview"] is False and d["mode"] == "probe"
    assert d["entry"] == "p4_probe.sh" and d["spec_file"] == L.PROBE_SPEC_FILE
    assert d["inputs"] == list(L.PROBE_TRANSFER_INPUTS) and d["outputs"][-1] == L.DIRECT_LAUNCH_FILE
    assert d["host"]["container_runtime"] == "docker" and d["host"]["ssh_alias"] == "experiment_zhixu"
    assert d["image_digest"] == L.IMAGE_V22 and d["gpu_name"] == ADA_NAME and d["submit_marker"] is None
    assert d["walltime_bound_s"] == L.PROBE["walltime_s"] and "R1-NO-TIMEOUT" in d["walltime_rule"]
    job = json.loads(RJ.render_direct(_launch_spec(sha), "kev-4b", ADA, mode="job", repo=repo))
    assert job["entry"] == "p4_job.sh" and job["inputs"] == list(L.TRANSFER_INPUTS)
    assert job["submit_marker"] == "P4_SUBMIT_STARTED_kev-4b.json"
    with pytest.raises(L.Stop, match="is not hosts.ada_rtx6000.host_config"):
        RJ.render_direct(_probe_spec("0" * 64), "kev-0.8b", ADA, mode="probe", repo=repo)
    with pytest.raises(L.Stop, match="not filled"):          # the shipped (placeholder) config
        RJ.render_direct(_probe_spec(_sha((ROOT / L.ADA_HOST_CONFIG).read_bytes())), "kev-0.8b", ADA,
                         mode="probe", repo=ROOT)
    preview = json.loads(RJ.render_direct(_probe_spec("0" * 64), "kev-0.8b", ADA, mode="probe", preview=True,
                                          repo=ROOT))
    assert preview["preview"] is True                         # never launched (load_descriptor)
    with pytest.raises(L.Stop, match="starts by direct"):
        RJ.render(_launch_spec(sha), "kev-0.8b", host_class=ADA)


def test_the_htcondor_jdl_tells_the_job_its_class():
    s = _launch_spec("a" * 64, (H200,))
    jdl = RJ.render(s, "kev-4b")
    assert "arguments = p4_spec.json kev-4b nemo2_h200" in jdl and 'GPUs_DeviceName =?= "NVIDIA H200"' in jdl
    text = (PKG / "p4_job.sh").read_text()
    assert '[ "$#" -eq 3 ]' in text and '--host-class "$3"' in text
    assert '--host-class "$3"' in (PKG / "p4_probe.sh").read_text()
    for sh in ("p4_job.sh", "p4_probe.sh"):
        assert subprocess.run(["bash", "-n", str(PKG / sh)]).returncode == 0


def _stage(tmp_path: Path, repo: Path, spec: dict, arm="kev-0.8b", mode="probe") -> Path:
    """A minimal direct stage by hand: the descriptor, the transferred inputs (synthetic bytes), p4_direct.py and the
    manifest (what p4_render_jdl writes; the full staging path is tested with the switch in the runner tests)."""
    st = tmp_path / f"stage_{arm}_{mode}"
    st.mkdir()
    desc = f"p4direct_{arm}.json"
    (st / desc).write_text(RJ.render_direct(spec, arm, ADA, mode=mode, repo=repo))
    inputs = L.PROBE_TRANSFER_INPUTS if mode == "probe" else L.TRANSFER_INPUTS
    for name in inputs:
        (st / name).write_text(json.dumps(spec) if name.endswith("spec.json") else f"{name}\n")
    shutil.copy2(PKG / "p4_direct.py", st / "p4_direct.py")
    files = {n: _sha((st / n).read_bytes()) for n in (desc, *inputs, "p4_direct.py")}
    (st / "STAGE_MANIFEST.json").write_text(json.dumps({"schema": "x", "preview": False, "files": files}))
    return st


class _Host:
    """Fakes for the host: nvidia-smi (one card, its other processes), the runtime's --version, a clock, and the
    container (it writes the job's outputs, advances the clock and checks that the lease is held)."""

    def __init__(self, name=ADA_NAME, cap="8.9", free=48000, others="", rc=0, hours=0.01, seconds=7200.0,
                 record_over=None):
        self.name, self.cap, self.free, self.others, self.rc = name, cap, free, others, rc
        self.hours, self.seconds, self.record_over = hours, seconds, record_over or {}
        self.t = 1_800_000_000.0
        self.calls, self.argv, self.env, self.running = [], None, None, ""

    def now(self):
        return self.t

    def run(self, argv):
        self.calls.append(argv)
        if argv[0] == "nvidia-smi" and argv[1].startswith("--id="):
            i = argv[1].split("=")[1]
            return _res(0, f"{i}, {UUID}, {self.name}, {self.cap}, 550.54, 49140 MiB, {self.free} MiB\n")
        if argv[0] == "nvidia-smi":
            return _res(0, self.others)
        if argv[1:] == ["--version"]:
            return _res(0, f"{argv[0]} version 1.2.3\n")
        if argv[:2] == ["docker", "ps"]:
            return _res(0, self.running)
        return _res(0)

    def popen(self, argv, cwd=None, env=None, pass_fds=(), start_new_session=False):
        self.argv, self.env, self.pass_fds, host = argv, env, pass_fds, self
        self.start_new_session = start_new_session
        lock = Path(json.loads(Path(cwd, L.DIRECT_LAUNCH_FILE).read_text())["lease"]["lock_path"])

        class Proc:
            def wait(self_):
                with pytest.raises(D.Refusal, match="held by another job"):      # the lease is ours while it runs
                    D.take_lease(str(lock))
                spec = json.loads(Path(cwd, argv[-3]).read_text())
                rec = {"schema": L.PROBE_RECORD_SCHEMA if spec.get("probe") else L.RECORD_SCHEMA, "mode": "probe",
                       "label": L.ENGINEERING_ONLY, "run_id": spec["run_id"], "arm": argv[-2], "host_class": argv[-1],
                       "gpu": {"name": ADA_NAME, "uuid": UUID, "compute_capability": "8.9", "driver": "550.54"},
                       "image": {"digest": spec["image"]["digest"]}, "gpu_hours": host.hours, "stop": None,
                       "stop_class": None, "steps": ["identity", "probe"], **host.record_over}
                Path(cwd, "job_record.json").write_text(json.dumps(rec))
                Path(cwd, "out.tar").write_bytes(b"tar")
                Path(cwd, "SHA256SUMS").write_text(
                    "".join(f"{_sha(Path(cwd, n).read_bytes())}  {n}\n" for n in ("out.tar", "job_record.json")))
                Path(cwd, "p4_run.log").write_text("P4 probe container job start\n")
                host.t += host.seconds
                return host.rc

            def terminate(self_):
                pass
        return Proc()


def _launch(stage, host, arm="kev-0.8b", gpu=3, hostname="ucrtasl"):
    return D.Launch(str(stage), arm, gpu, run=host.run, popen=host.popen, hostname=hostname, now=host.now,
                    environ={"USER": "dowling", "PATH": "/usr/bin"}).main()


def test_the_launcher_leases_runs_the_pinned_container_on_the_leased_card_and_records_it(ada_repo, tmp_path):
    repo, sha = ada_repo
    ps = _probe_spec(sha)
    st = _stage(tmp_path, repo, ps)
    host = _Host()
    out = _launch(st, host)
    assert out["status"] == "finished" and out["exit_code"] == 0 and out["wall_clock_s"] == 7200.0
    job = Path(out["job_dir"])
    assert job.parent == tmp_path / "work" / ps["run_id"] / "kev-0.8b" and job.name.startswith("20270115T")
    for name in L.PROBE_TRANSFER_INPUTS:                      # the staged inputs, copied in
        assert (job / name).read_bytes() == (st / name).read_bytes()
    rec = json.loads((job / L.DIRECT_LAUNCH_FILE).read_text())
    assert rec["schema"] == L.DIRECT_LAUNCH_SCHEMA == D.LAUNCH_SCHEMA and rec["status"] == "finished"
    assert rec["gpu"]["uuid"] == UUID and rec["gpu"]["name"] == ADA_NAME and rec["lease"]["gpu_index"] == 3
    assert rec["lease"]["lock_path"] == str(tmp_path / "locks" / "gpu3.lock")
    assert rec["runtime"] == "docker" and rec["runtime_version"] == "docker version 1.2.3"
    assert rec["image_digest"] == L.IMAGE_V22 and rec["hostname"] == "ucrtasl" and rec["host_class"] == ADA
    assert rec["other_processes_start"] == {"count": 0, "memory_mib": 0.0} and rec["card_shared"] is False
    assert rec["other_processes_end"] == {"count": 0, "memory_mib": 0.0}               # R1-CARD-SHARE (4)
    assert rec["timeout"].startswith("none") and rec["stage"]["manifest_sha256"] == \
        _sha((st / "STAGE_MANIFEST.json").read_bytes())
    argv = host.argv
    assert argv[:3] == ["docker", "run", "--rm"] and f"device={UUID}" in argv and L.IMAGE_V22 in argv
    assert argv[argv.index("--user") + 1].split(":")[0] != "0" and argv[argv.index("-w") + 1] == str(job)
    assert argv[-4:] == ["p4_probe.sh", L.PROBE_SPEC_FILE, "kev-0.8b", ADA]
    assert f"{L.LEASED_GPU_ENV}={UUID}" in argv and f"CUDA_VISIBLE_DEVICES={UUID}" in argv
    # once per stage; the lease is released
    again = _launch(st, _Host())
    assert again["status"] == "refused" and "already launched" in again["refusal"]
    D.take_lease(str(tmp_path / "locks" / "gpu3.lock")).close()
    assert set(out["outputs"]) == {str(job / n) for n in D.OUTPUTS}


def test_the_launcher_refusals(ada_repo, tmp_path):
    repo, sha = ada_repo
    ps = _probe_spec(sha)
    cases = ((dict(hostname="tasl-7"), "this host is 'tasl-7'"),
             (dict(host=_Host(name="NVIDIA H200", cap="9.0")), "not the class's"),
             (dict(host=_Host(free=1000)), "1000.0 MiB free, the job needs 40000 MiB"))
    for k, (kw, match) in enumerate(cases):
        st = _stage(tmp_path / f"c{k}", repo, ps) if (tmp_path / f"c{k}").mkdir() is None else None
        out = _launch(st, kw.get("host", _Host()), hostname=kw.get("hostname", "ucrtasl"))
        assert out["status"] == "refused" and match in out["refusal"], out
    # lease busy: refused (exit 75), never shared between two of our jobs
    (tmp_path / "busy").mkdir()
    st = _stage(tmp_path / "busy", repo, ps)
    (tmp_path / "locks").mkdir(exist_ok=True)
    held = D.take_lease(str(tmp_path / "locks" / "gpu3.lock"))
    out = _launch(st, _Host())
    held.close()
    assert out["status"] == "refused" and out["exit_code"] == D.LEASE_BUSY_EXIT and out["wall_clock_s"] == 0.0
    assert out["job_dir"] is None and not (tmp_path / "work").exists()        # review M2: nothing written
    assert not (st / "P4_DIRECT_LAUNCHED_kev-0.8b.json").exists()
    assert _launch(st, _Host())["status"] == "finished"                     # the stage stays launchable
    # review M1: a P.4 docker container still running on the card (its launcher was killed) is refused
    (tmp_path / "dock").mkdir()
    st = _stage(tmp_path / "dock", repo, ps)
    busy_host = _Host()
    busy_host.running = "p4-x-kev-0.8b-old\n"
    out = _launch(st, busy_host)
    assert out["status"] == "refused" and "still runs on card 3" in out["refusal"] and out["job_dir"] is None
    assert ["docker", "ps", "--filter", f"label={D.DOCKER_LABEL}={UUID}", "--format", "{{.Names}}"] in busy_host.calls
    # a changed staged file, a preview descriptor, another runtime, an unpinned image
    (tmp_path / "chg").mkdir()
    st = _stage(tmp_path / "chg", repo, ps)
    (st / "proposals.jsonl").write_text("changed\n")
    assert "changed after staging" in _launch(st, _Host())["refusal"]
    for edit, match in ((lambda d: d.update(preview=True), "preview"),
                        (lambda d: d["host"].update(container_runtime="podman"), "not one of"),
                        (lambda d: d.update(image_digest="ghcr.io/dowlingwong/r1-htc-gpu:latest"), "by digest"),
                        (lambda d: d["host"].update(work_root="relative/dir"), "absolute path"),
                        (lambda d: d["host"].update(min_free_mib="0"), "min_free_mib")):
        d = json.loads(RJ.render_direct(ps, "kev-0.8b", ADA, mode="probe", repo=repo))
        edit(d)
        p = tmp_path / "desc"
        p.mkdir(exist_ok=True)
        (p / "p4direct_kev-0.8b.json").write_text(json.dumps(d))
        with pytest.raises(D.Refusal, match=match):
            D.load_descriptor(str(p), "kev-0.8b")


def test_rows_g_the_launcher_shares_a_card_with_enough_free_memory(ada_repo, tmp_path):
    repo, sha = ada_repo
    st = _stage(tmp_path, repo, _probe_spec(sha))
    host = _Host(free=45000, others=f"{UUID}, 999, 3000\n")
    out = _launch(st, host)
    rec = json.loads(Path(out["job_dir"], L.DIRECT_LAUNCH_FILE).read_text())
    assert out["status"] == "finished" and rec["card_shared"] is True and rec["memory_needed_mib"] == 40000
    assert rec["other_processes_start"] == {"count": 1, "memory_mib": 3000.0}


def test_a_p4_job_launches_only_from_a_stage_the_switch_submitted(ada_repo, tmp_path):
    repo, sha = ada_repo
    s = _launch_spec(sha)
    st = _stage(tmp_path, repo, s, arm="kev-4b", mode="job")
    out = _launch(st, _Host(), arm="kev-4b")
    assert out["status"] == "refused" and "no switch marker" in out["refusal"] and out["job_dir"] is None
    msha = _sha((st / "STAGE_MANIFEST.json").read_bytes())
    marker = st / "P4_SUBMIT_STARTED_kev-4b.json"
    marker.write_text(json.dumps({"arm": "kev-4b", "launch_kind": "direct", "stage_manifest_sha256": "0" * 64}))
    assert "does not name" in _launch(st, _Host(), arm="kev-4b")["refusal"]
    marker.write_text(json.dumps({"arm": "kev-4b", "launch_kind": "direct", "stage_manifest_sha256": msha}))
    host = _Host(record_over={"schema": L.RECORD_SCHEMA, "mode": None, "steps": ["identity", "test_path"]})
    out = _launch(st, host, arm="kev-4b")
    rec = json.loads(Path(out["job_dir"], L.DIRECT_LAUNCH_FILE).read_text())
    assert out["status"] == "finished" and rec["mode"] == "job" and rec["stage"]["submit_marker_sha256"] == \
        _sha(marker.read_bytes())
    assert host.argv[-4:] == ["p4_job.sh", "p4_spec.json", "kev-4b", ADA]


def test_a_signal_stops_the_container_and_is_recorded_as_interrupted(ada_repo, tmp_path):
    repo, sha = ada_repo
    st = _stage(tmp_path, repo, _probe_spec(sha))
    host = _Host()
    launch = D.Launch(str(st), "kev-0.8b", 0, run=host.run, popen=host.popen, hostname="ucrtasl", now=host.now,
                      environ={})
    real_popen = host.popen

    def popen(argv, cwd=None, env=None, pass_fds=()):
        proc = real_popen(argv, cwd=cwd, env=env, pass_fds=pass_fds)
        inner = proc.wait

        def wait():
            inner()
            launch._on_signal(15, None)
            return -15
        proc.wait = wait
        return proc
    launch.popen = popen
    out = launch.main()
    rec = json.loads(Path(out["job_dir"], L.DIRECT_LAUNCH_FILE).read_text())
    assert out["status"] == "interrupted" and rec["exit_code"] == -15 and "signal 15" in rec["refusal"]
    assert ["docker", "kill", rec["command"][rec["command"].index("--name") + 1]] in host.calls
    assert rec["wall_clock_s"] == 7200.0                      # charged as recorded; the attempt is repeated


def test_the_apptainer_command_scopes_the_card_and_unknown_runtimes_are_refused():
    desc = {"host": {"container_runtime": "apptainer", "shm_size": "16g"}, "image_digest": L.IMAGE_V22,
            "entry": "p4_probe.sh", "spec_file": L.PROBE_SPEC_FILE, "arm": "kev-0.8b", "host_class": ADA}
    argv, env = D.container_argv(desc, "/w/job", UUID, 1000, 1000, "n")
    assert argv[:5] == ["apptainer", "exec", "--nv", "--nvccli", "--containall"] and env == \
        {"NVIDIA_VISIBLE_DEVICES": UUID}
    assert "docker://" + L.IMAGE_V22 in argv and f"{L.LEASED_GPU_ENV}={UUID}" in argv and "--pwd" in argv
    assert argv[-4:] == ["p4_probe.sh", L.PROBE_SPEC_FILE, "kev-0.8b", ADA]
    with pytest.raises(D.Refusal, match="not one of"):
        D.container_argv({**desc, "host": {"container_runtime": "singularity"}}, "/w", UUID, 1, 1, "n")


@pytest.mark.parametrize("mode", ["probe", "job"])
def test_ada_venv_uses_the_same_entry_under_the_lease_and_seals_as_venv(tmp_path, mode):
    repo = tmp_path / "repo"
    config = repo / L.ADA_HOST_CONFIG
    config.parent.mkdir(parents=True)
    shutil.copy2(ROOT / L.ADA_HOST_CONFIG, config)
    values = tmp_path / "fill.json"
    values.write_text(json.dumps(_ada_values(str(tmp_path / "work"), str(tmp_path / "locks"),
                                            **{"direct.container_runtime": "venv", "direct.ssh_alias": "ada_server"})))
    config_sha = FH.fill(values, config)["sha256"]
    spec = _probe_spec(config_sha) if mode == "probe" else _launch_spec(config_sha)
    stage = _stage(tmp_path, repo, spec, mode=mode)
    if mode == "job":
        (stage / "P4_SUBMIT_STARTED_kev-0.8b.json").write_text(
            json.dumps({"arm": "kev-0.8b", "launch_kind": "direct",
                        "stage_manifest_sha256": _sha((stage / "STAGE_MANIFEST.json").read_bytes())}))
    desc = D.load_descriptor(str(stage), "kev-0.8b")
    assert desc["host"]["ssh_alias"] == "ada_server"
    venv = desc["host"]["venv"]
    assert venv["version"] == "3.12.10"
    freeze = {"status": "identical", "pinned_sha256": L.ENV3_FREEZE_SHA256, "venv_freeze_sha256": "a" * 64,
              "sha256_sorted": L.ENV3_FREEZE_SORTED_SHA256}
    record_over = {"venv": venv, "image": None, "env3_freeze": freeze}
    if mode == "job":
        record_over.update(mode=None, steps=["identity", "test_path"],
                           spec_sha256=_sha((stage / "p4_spec.json").read_bytes()))
    host = _Host(record_over=record_over)
    run = host.run
    host.run = lambda argv: _res(0, "Python 3.12.10\n") if argv == [venv["python"], "--version"] else run(argv)
    launch = D.Launch(str(stage), "kev-0.8b", 3, run=host.run, popen=host.popen, hostname="ucrtasl", now=host.now,
                      environ={"PATH": "/usr/bin", "PYTHONPATH": "/wrong", "HF_TOKEN": "fixture"})
    out = launch.main()
    assert out["status"] == "finished"
    assert host.argv == ["/bin/bash", D.MODES[mode], D.SPEC_FILES[mode], "kev-0.8b", ADA]
    assert host.start_new_session and host.env[D.VENV_LEASE_FD_ENV] == str(host.pass_fds[0])
    assert len(host.pass_fds) == 1 and host.env["P4_VENV_PYTHON"] == venv["python"]
    assert host.env[L.LEASED_GPU_ENV] == host.env["CUDA_VISIBLE_DEVICES"] == UUID
    assert not {"PYTHONPATH", "HF_TOKEN"} & host.env.keys()
    job = Path(out["job_dir"])
    record = json.loads((job / L.DIRECT_LAUNCH_FILE).read_text())
    assert record["runtime"] == "venv" and record["venv"] == venv and record["image_executed"] is False
    sealed_root = tmp_path / "sealed"
    receipt = L.seal(job, spec, "kev-0.8b", sealed_root)
    assert receipt["identity_verified"] is True
    if mode == "job":
        first_record = Path(receipt["sealed_path"]) / "job_record.json"
        assert SW.check_first_record(first_record, spec, record_over["spec_sha256"], sealed_root)
    bad = {**freeze, "status": "causal_conv1d_only"}
    assert not L.launch_runtime_verified(record, {"host_class": ADA, "venv": venv, "env3_freeze": bad}, spec)
    record.update(status="interrupted", refusal="STOP: native launcher interrupted")
    (job / L.DIRECT_LAUNCH_FILE).write_text(json.dumps(record))
    interrupted = L.seal(job, spec, "kev-0.8b", tmp_path / "interrupted")
    assert interrupted["identity_verified"] is False
    assert interrupted["stop"] == "STOP: native launcher interrupted"
    assert interrupted["stop_class"] == "infrastructure"
    assert interrupted["charge_basis"].startswith("incomplete launcher record")


def test_ada_venv_requires_exact_lock_and_cuda_uuid(monkeypatch):
    python = "/test/ada/venv/bin/python"
    monkeypatch.setenv("P4_VENV_PYTHON", python)
    pinned = (ROOT / L.ENV3_FREEZE).read_text()
    calls = []

    def freeze_command(argv, **kwargs):
        calls.append(argv)
        return _res(0, pinned)

    recorded = L.env3_freeze(SPEC, ROOT, freeze_command)
    assert calls == [["uv", "pip", "freeze", "--python", python]]
    assert recorded["status"] == "identical" and recorded["venv_freeze_sha256"] == _sha(pinned.encode())
    with pytest.raises(L.Stop, match="venv freeze must equal"):
        L.env3_freeze(SPEC, ROOT, lambda *a, **k: _res(0, pinned.replace("causal-conv1d==1.7.0",
                                                                        "causal-conv1d==1.7.0+local")))
    monkeypatch.setenv(L.LEASED_GPU_ENV, UUID)
    with pytest.raises(L.Stop, match="bind CUDA visibility"):
        L.gpu_identity(host_class=ADA)
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", UUID)

    def gpu_command(argv, **kwargs):
        assert argv[1] == f"--id={UUID}"
        return _res(0, f"{ADA_NAME}, {UUID}, 550.54, 49140 MiB, 8.9\n")

    gpu = L.gpu_identity(gpu_command, host_class=ADA)
    L.check_venv_gpu(gpu, lambda *a, **k: _res(0, UUID + "\n"))
    with pytest.raises(L.Stop, match="exactly the leased GPU"):
        L.check_venv_gpu(gpu, lambda *a, **k: _res(0, "GPU-other\n"))


def test_native_interrupt_signals_the_job_group_and_training_inherits_the_lease(monkeypatch, tmp_path):
    import signal
    from types import SimpleNamespace

    calls = []
    launch = D.Launch(str(tmp_path), "kev-0.8b", 3)
    launch.record = {"runtime": "venv"}
    launch.proc = SimpleNamespace(pid=12345)
    monkeypatch.setattr(D.os, "killpg", lambda group, sig: calls.append((group, sig)))
    launch._on_signal(signal.SIGINT, None)
    assert calls == [(12345, signal.SIGTERM)]
    monkeypatch.setenv("P4_VENV_PYTHON", "/test/ada/venv/bin/python")
    with D.take_lease(str(tmp_path / "gpu3.lock")) as lease:
        monkeypatch.setenv(L.VENV_LEASE_FD_ENV, str(lease.fileno()))
        monkeypatch.setattr(L.subprocess, "run", lambda argv, **kw: calls.append(kw["pass_fds"]) or _res())
        L._sh(["synthetic-training"])
        assert calls[-1] == (lease.fileno(),)
    with pytest.raises(L.Stop, match="did not inherit"):
        L._sh(["synthetic-training"])


def test_list_cards_shows_free_memory_and_other_processes():
    host = _Host(others=f"{UUID}, 1, 100\n")
    host.run = lambda argv: _res(0, f"0, {UUID}, {ADA_NAME}, 8.9, 550, 49140 MiB, 1000 MiB\n") \
        if argv[1].startswith("--query-gpu") else _res(0, f"{UUID}, 1, 100\n")
    cards = D.list_cards(host.run)
    assert cards[0]["memory_free_mib"] == 1000.0 and cards[0]["other_processes"] == {"count": 1, "memory_mib": 100.0}


# ============================================================================================ seal and charges
def _launched(ada_repo, tmp_path, **host_kw) -> tuple[dict, Path]:
    repo, sha = ada_repo
    ps = _probe_spec(sha)
    st = _stage(tmp_path, repo, ps)
    out = _launch(st, _Host(**host_kw))
    return ps, Path(out["job_dir"])


def test_seal_accepts_a_direct_attempt_and_charges_its_launcher_wall_clock(ada_repo, tmp_path):
    ps, job = _launched(ada_repo, tmp_path)
    receipt = L.seal(job, ps, "kev-0.8b", tmp_path / "sealed")
    assert receipt["launch"] == "direct" and receipt["identity_verified"] is True and receipt["host_class"] == ADA
    assert receipt["charged_gpu_hours"] == 2.0 and receipt["charge_basis"].startswith("max(direct launcher wall clock")
    assert receipt["direct_launch_sha256"] == _sha((job / L.DIRECT_LAUNCH_FILE).read_bytes())
    assert receipt["gpu_uuid"] == UUID and receipt["other_processes_start"]["count"] == 0
    sealed = Path(receipt["sealed_path"])
    assert (sealed / L.DIRECT_LAUNCH_FILE).read_bytes() == (job / L.DIRECT_LAUNCH_FILE).read_bytes()
    charged = L.charged_hours(ps, tmp_path / "sealed")
    assert charged["attempts"][0]["launch"] == "direct" and charged["total"] == 2.0
    pc = L.probe_charges(tmp_path / "sealed")                 # R1-HOST-FREE (5): no RemoteWallClockTime needed
    a = pc["runs"][ps["run_id"]]["attempts"][0]
    assert a["charge_basis"] == "receipt (direct launcher record)" and pc["unrecorded"] == [] and pc["total"] == 2.0
    with pytest.raises(L.Stop, match="exactly its sealed HTCondor attempts"):
        L.probe_charges(tmp_path / "sealed", wallclock={"schema": L.WALLCLOCK_SCHEMA, "runs": {
            ps["run_id"]: {"kev-0.8b/attempt-1": {"cluster_id": "1", "remote_wallclock_s": 1.0}}}})
    docs = L.charge_file_docs(pc, ps["run_id"])
    assert docs[ps["run_id"]]["attempts"]["kev-0.8b/attempt-1"]["launch"] == "direct"
    L.write_charge_files(docs, tmp_path / "sealed")
    again = L.probe_charges(tmp_path / "sealed")              # applied from the charge file, still direct
    assert again["runs"][ps["run_id"]]["attempts"][0]["charge_basis"] == "_wallclock.json" and again["total"] == 2.0


def test_seal_takes_the_record_hours_when_larger_and_bounds_an_incomplete_launcher_record(ada_repo, tmp_path):
    ps, job = _launched(ada_repo, tmp_path, hours=3.5)
    assert L.seal(job, ps, "kev-0.8b", tmp_path / "s1")["charged_gpu_hours"] == 3.5
    rec = json.loads((job / L.DIRECT_LAUNCH_FILE).read_text())
    rec.update(ended_utc=None, wall_clock_s=None, exit_code=None, status="running")   # the launcher was killed
    (job / L.DIRECT_LAUNCH_FILE).write_text(json.dumps(rec))
    got = L.seal(job, ps, "kev-0.8b", tmp_path / "s2")
    span = (L.time.time() - L._utc_epoch(rec["started_utc"])) / 3600
    assert got["charged_gpu_hours"] >= max(span - 0.01, 2.0) and got["identity_verified"] is False
    assert got["charge_basis"].startswith("incomplete launcher record")
    rec["started_utc"] = "yesterday"
    (job / L.DIRECT_LAUNCH_FILE).write_text(json.dumps(rec))
    with pytest.raises(L.Stop, match="cannot be bounded"):
        L.seal(job, ps, "kev-0.8b", tmp_path / "s3")


def test_seal_refuses_a_direct_attempt_that_is_not_this_one(ada_repo, tmp_path):
    ps, job = _launched(ada_repo, tmp_path)
    good = (job / L.DIRECT_LAUNCH_FILE).read_text()
    for edit, match in ((lambda r: r.update(arm="kev-4b"), "run_id/arm"),
                        (lambda r: r.update(mode="job"), "mode"),
                        (lambda r: r.update(host_class=H200), "not a direct class"),
                        (lambda r: r.update(image_digest="x"), "image_digest"),
                        (lambda r: r["gpu"].update(uuid="GPU-another"), "leased card")):
        r = json.loads(good)
        edit(r)
        (job / L.DIRECT_LAUNCH_FILE).write_text(json.dumps(r))
        with pytest.raises(L.Stop, match=match):
            L.seal(job, ps, "kev-0.8b", tmp_path / "sx")
    (job / L.DIRECT_LAUNCH_FILE).write_text("{not json")
    with pytest.raises(L.Stop, match="not a readable launcher record"):
        L.seal(job, ps, "kev-0.8b", tmp_path / "sx")
    (job / L.DIRECT_LAUNCH_FILE).unlink()                      # the record names a direct class: nothing bounds it
    with pytest.raises(L.Stop, match="direct_launch.json is missing"):
        L.seal(job, ps, "kev-0.8b", tmp_path / "sx")
    assert not (tmp_path / "sx").exists() or not any((tmp_path / "sx").rglob("SEAL_RECEIPT.json"))


def test_rows_g_an_oom_beside_another_process_is_sealed_as_infrastructure(ada_repo, tmp_path):
    ps, job = _launched(ada_repo, tmp_path, free=45000, others=f"{UUID}, 7, 2000\n",
                        record_over={"stop": "STOP: CUDA OOM in sft-dev at micro-batch 8", "stop_class": "arm",
                                     "steps": ["identity"]})
    got = L.seal(job, ps, "kev-0.8b", tmp_path / "sealed")
    assert got["stop_class"] == "infrastructure" and got["lost_beside_another_process"] is True
    assert "R1-CARD-SHARE (3)" in got["stop"] and got["card_shared"] is True
    ps2, job2 = _launched(ada_repo, tmp_path / "alone", record_over={
        "stop": "STOP: CUDA OOM", "stop_class": "arm", "steps": ["identity"]}) if (tmp_path / "alone").mkdir() is None \
        else (None, None)
    alone = L.seal(job2, ps2, "kev-0.8b", tmp_path / "sealed2")
    assert alone["stop_class"] == "arm" and "lost_beside_another_process" not in alone


def test_review_m2_a_refusal_before_the_claim_writes_nothing_and_m9_m1_dirs_and_lease_fd(ada_repo, tmp_path):
    repo, sha = ada_repo
    ps = _probe_spec(sha)
    st = _stage(tmp_path, repo, ps)
    out = _launch(st, _Host(free=10))
    assert out["status"] == "refused" and out["refusal"].startswith("STOP: card 3 has 10.0 MiB free")
    assert out["job_dir"] is None and not (st / "P4_DIRECT_LAUNCHED_kev-0.8b.json").exists()
    host = _Host()
    out = _launch(st, host)                                  # the same stage, now with a card that fits
    job = Path(out["job_dir"])
    assert out["status"] == "finished" and (st / "P4_DIRECT_LAUNCHED_kev-0.8b.json").is_file()
    for d in (job, job.parent, job.parent.parent):           # review M9: every level created 0700
        assert d.stat().st_mode & 0o777 == 0o700, d
    assert len(host.pass_fds) == 1                           # review M1: the container inherits the lease
    assert "--label" in host.argv and f"{D.DOCKER_LABEL}={UUID}" in host.argv


# ============================================================================================ the switch's key lines
def _fields(s: dict, spec_sha: str, **over) -> dict:
    """A complete note key block for a launch spec (the runner tests' _note_fields, for any admitted classes)."""
    hc = " ".join(f"{h['host_config']['path']} sha256 {h['host_config']['sha256']}" for h in s["hosts"].values())
    host = "R1-HOST-FREE: GPU model recorded per job, not fixed; one card per arm; admitted: " + ", ".join(
        f"{c} ({L.HOST_CLASSES[c]['gpu_name']})" for c in s["hosts"])
    f = {"approved": "true", "label": "ENGINEERING_ONLY", "phase": "1", "run_id": s["run_id"], "spec_sha256": spec_sha,
         "code_commit": s["paper"]["commit"], "versions_sha256": s["image"]["versions_sha256"],
         "labels": f"/r/sweep1/traindev/label_block.traindev.jsonl sha256 {s['labels']['partition_sha256']}",
         "label_receipt": f"/r/sweep1/traindev/RECEIPT.json sha256 {s['labels']['receipt_sha256']}",
         "source_label_block": L.SOURCE_BLOCK_SHA256,
         "label_freeze": f"{s['labels']['freeze_record']['path']} sha256 {s['labels']['freeze_record']['sha256']}",
         "split_file": f"{L.SPLIT_FILE['path']} sha256 {L.SPLIT_FILE['sha256']}", "host_config": hc,
         "image": s["image"]["digest"], "env3_freeze": f"{L.ENV3_FREEZE} R1-TRACKP-V21-FREEZE "
                                                     "R1-TRACKP-P4-RUNNER-DECISIONS",
         "gpu_hours_cap": "40 (P4-CAP A; P4-PROBECAP A: probe_gpu_hours: 0.50, T1 included, P4-T1CHARGE A; "
                          "GPU-hours on any card, R1-HOST-FREE (5)); slot_hours_cap: 64",
         "job_layout": "one job per base", "table_pin": L.TABLE_PIN, "duplicate_policy": "heldout_excludes_seen",
         "split": "P3, P4-P1SPLIT A", "lr_grid": "1e-5,3e-5,1e-4; seeds per lr: 3; 250, 500; 20261122",
         "host": host, "harness_commit": "none",
         "h200_sft_probe": "none: the spec does not admit nemo2_h200", "ada_sft_probe": "none: not admitted",
         "h200_smoke_e0": "none: the spec does not admit nemo2_h200", "ada_smoke_e0": "none: not admitted",
         "label_table_binding": f"P4-F2 A {L.SEALED_V2_PROPOSALS_SHA256} {L.V3_PROPOSALS_SHA256} "
                                f"{L.FEAT_ONE_IDENTITY['path']} {L.FEAT_ONE_IDENTITY['sha256']}",
         "probe_charge_files": "trackp-p4-probe-20261125-a " + "9" * 64,
         "arms": ", ".join(s["arms"]), "micro_batch": "8"}
    for c in s["hosts"]:
        f[L.HOST_CLASSES[c]["probe_label"]] = SW.probe_record(s, c)
        f[L.HOST_CLASSES[c]["smoke_label"]] = f"docs/r1/reports/{c}_smoke.md and docs/r1/reports/{c}_e0.md"
    f.update(over)
    return f


@pytest.mark.parametrize("classes", [(ADA,), (ADA, H200)])
def test_switch_host_lines_name_the_admitted_classes_and_their_probe_records(classes):
    s = _launch_spec("a" * 64, classes)
    SW.check_binding(_fields(s, "b" * 64), s, "b" * 64)
    assert SW.P_CITES["P8"] == ("R1-T1-HOST-TASL", "R1-HOST-FREE")
    host = _fields(s, "b" * 64)["host"]
    for over, match in (
            ({"host": "NEMO2 H200 (HTCondor), R1-T1-HOST-TASL"}, "note host must contain 'R1-HOST-FREE'"),
            ({"host": host.replace(ADA_NAME, "RTX")}, f"must contain '{ADA_NAME}'"),
            ({"host": host.replace("one card", "one GPU")}, "must contain 'one card'"),
            ({"host_config": L.HOST_CONFIG + " " + "5" * 64}, "note host_config must contain"),
            ({"ada_sft_probe": "docs/r1/reports/other.md"}, "note ada_sft_probe must contain"),
            ({"gpu_hours_cap": "40 (P4-CAP A; P4-PROBECAP A: probe_gpu_hours: 0.50, P4-T1CHARGE A); "
                               "slot_hours_cap: 64"}, r"R1-HOST-FREE \(5\)")):
        with pytest.raises(SW.Stop, match=match):
            SW.check_binding(_fields(s, "b" * 64, **over), s, "b" * 64)
    if H200 not in classes:                                   # a probe line of a class not admitted reads none
        with pytest.raises(SW.Stop, match="h200_sft_probe must read none"):
            SW.check_binding(_fields(s, "b" * 64, h200_sft_probe="docs/r1/reports/h.md"), s, "b" * 64)
    fields = _fields(s, "b" * 64)
    fields.pop("ada_sft_probe")
    with pytest.raises(SW.Stop, match="ada_sft_probe"):
        SW.check_binding(fields, s, "b" * 64)
    # review B1 (R1-QTORCH-AMEND): every admitted class's smoke and E0 records, never another class's
    for line in ("none: not yet", "the H200 records", ""):
        with pytest.raises(SW.Stop, match="ada_smoke_e0 must cite the Track P smoke and E0 records"):
            SW.check_binding(_fields(s, "b" * 64, ada_smoke_e0=line), s, "b" * 64)
    if H200 not in classes:
        with pytest.raises(SW.Stop, match="h200_smoke_e0 must read none"):
            SW.check_binding(_fields(s, "b" * 64, h200_smoke_e0="docs/r1/reports/h.md"), s, "b" * 64)
    assert SW.smoke_records("docs/r1/reports/a.md (smoke 1), docs/r1/reviews/b.md") == \
        ["docs/r1/reports/a.md", "docs/r1/reviews/b.md"] and SW.smoke_records("none: docs/r1/x.md") == []


def test_switch_probe_hours_are_per_class():
    s = _launch_spec("a" * 64, (ADA, H200))
    text = f"p4_probe_host_class: {ADA}\n" + "".join(
        f"p4_estimate_hours: {a} {s['hosts'][ADA]['estimate']['hours'][a]}\n" for a in s["arms"])
    assert SW.check_probe_hours(text, s, ADA)["kev-4b"] == 6.64
    with pytest.raises(SW.Stop, match="name the host class"):
        SW.check_probe_hours(text, s)
    with pytest.raises(SW.Stop, match="p4_probe_host_class: nemo2_h200"):
        SW.check_probe_hours(text, s, H200)
    with pytest.raises(SW.Stop, match="found"):
        SW.check_probe_hours(text + f"p4_probe_host_class: {ADA}\n", s, ADA)


# ============================================================================================ the per-class fill hook
def test_fill_hook_h200_class_is_unchanged_and_ada_has_its_own_26_values(tmp_path):
    t = FH.template()
    assert t["schema"] == FH.SCHEMA and set(t["values"]) == FH.EXPECTED and len(FH.EXPECTED) == 19
    a = FH.template(ADA)
    assert a["schema"] == FH.SCHEMA_V2 and a["host_class"] == ADA and set(a["values"]) == FH.expected(ADA)
    assert len(FH.expected(ADA)) == 26 and a["values"]["gpu.name"] == ADA_NAME
    assert a["values"]["gpu.compute_capability"] == "8.9" and a["values"]["direct.ssh_alias"] == "experiment_zhixu"
    assert a["values"]["direct.container_runtime"].startswith("FILL")
    from r1.c3.train import run as R
    assert set(R.placeholders(json.loads((ROOT / L.ADA_HOST_CONFIG).read_text()))) == FH.expected(ADA)
    cfg = json.loads((ROOT / L.ADA_HOST_CONFIG).read_text())
    h200 = json.loads((ROOT / L.HOST_CONFIG).read_text())
    for key in ("bases", "code_pins", "lora", "lr_grid", "head_lr", "token_lr", "image", "e0", "spike"):
        for k in (h200[key] if isinstance(h200[key], dict) else [None]):
            if k is None:
                assert cfg[key] == h200[key], key
            elif not (key == "bases" and "local_path" in str(h200[key][k])):
                a_, b_ = dict(cfg[key][k]) if isinstance(cfg[key][k], dict) else cfg[key][k], h200[key][k]
                if isinstance(a_, dict):
                    a_ = {x: y for x, y in a_.items() if "local_path" not in x}
                    b_ = {x: y for x, y in b_.items() if "local_path" not in x}
                assert a_ == b_, (key, k)
    assert cfg["lease"] == "direct_gpu_lease" and cfg["sft"]["micro_batch"] == 8


@pytest.mark.parametrize("over, match", [
    ({"gpu.name": "NVIDIA H200"}, "gpu.name must be"),
    ({"gpu.compute_capability": "9.0"}, "compute_capability must be"),
    ({"direct.ssh_alias": "tasl7"}, "ssh_alias must be"),
    ({"direct.container_runtime": "podman"}, "must be one of"),
    ({"direct.work_root": "jobs"}, "not an absolute path"),
    ({"direct.lock_dir": "/data1/../etc"}, "not an absolute path"),
    ({"direct.hostname": "bad host"}, "does not match"),
    ({"direct.min_free_mib": "lots"}, "does not match"),
    ({"direct.shm_size": "FILL: 16g"}, "placeholder"),
])
def test_fill_hook_ada_refusals(tmp_path, over, match):
    cfg = tmp_path / "ada.json"
    shutil.copy2(ROOT / L.ADA_HOST_CONFIG, cfg)
    values = tmp_path / "v.json"
    values.write_text(json.dumps(_ada_values("/data1/dowling/r1_trackp_p4/jobs", "~/r1_locks", **over)))
    with pytest.raises(L.Stop, match=match):
        FH.fill(values, cfg, dry_run=True, host_class=ADA)


def test_fill_hook_ada_fills_exactly_and_names_its_class(ada_repo, tmp_path):
    repo, sha = ada_repo
    filled = json.loads((repo / L.ADA_HOST_CONFIG).read_text())
    assert filled["direct"]["container_runtime"] == "docker" and filled["gpu"]["name"] == ADA_NAME
    assert _sha((repo / L.ADA_HOST_CONFIG).read_bytes()) == sha
    values = tmp_path / "v.json"
    values.write_text(json.dumps(_ada_values("/data1/dowling/x", "~/r1_locks")))
    cfg = tmp_path / "ada.json"
    shutil.copy2(ROOT / L.ADA_HOST_CONFIG, cfg)
    with pytest.raises(L.Stop, match="not the input's class"):
        FH.fill(values, cfg, dry_run=True, host_class=H200)
    with pytest.raises(L.Stop, match="exactly the 26 known"):
        FH.fill(values, repo / L.ADA_HOST_CONFIG, dry_run=True)          # already filled: no second fill
    v1 = json.loads(values.read_text())
    v1["schema"] = FH.SCHEMA                                             # schema /1 is the H200 class
    values.write_text(json.dumps(v1))
    with pytest.raises(L.Stop, match="not the input's class nemo2_h200"):
        FH.fill(values, cfg, dry_run=True, host_class=ADA)
    assert FH.main(["--template", "--host-class", ADA]) == 0


def test_trackp_reads_the_direct_lease_like_an_exclusive_slot_without_the_foreign_process_check():
    text = (ROOT / "r1/scripts/trackp.py").read_text()
    assert 'direct = args.cfg.get("lease") == "direct_gpu_lease"' in text and "check_processes=not direct" in text



# ============================================================================================ review round 1
def test_review_b2_the_htcondor_jdl_requests_its_own_classes_walltime():
    s = _launch_spec("a" * 64, (ADA, H200))
    s["hosts"][ADA]["estimate"]["hours"]["kev-4b"] = 16.0           # Ada slower: max over classes = 88,200 s
    assert L.arm_walltime_s(s, "kev-4b") == 88200 > L.MAX_WALLTIME_S
    assert L.validate_spec(s, launch=True)["run_id"] == SPEC["run_id"]     # H200's own 6.64 h fits one HTCondor job
    own = L.arm_walltime_s(s, "kev-4b", H200)
    jdl = RJ.render(s, "kev-4b", host_class=H200)
    assert f"+RequestWalltime = {own}" in jdl and own <= L.MAX_WALLTIME_S and "88200" not in jdl
    assert json.loads(RJ.render_direct(s, "kev-4b", ADA, mode="job", preview=True, repo=ROOT))["walltime_bound_s"] \
        == 88200                                                            # the charge bound stays the largest


def test_review_m3_reaching_the_figure_is_reported():
    s = _launch_spec("a" * 64)
    p = L.projection(s)
    s["caps"]["probe_gpu_hours"] = round(40.0 - p["total_gpu_hours"], 2)
    got = L.validate_spec(s, launch=True)
    assert got["projection"]["total_with_probe_gpu_hours"] == 40.0 and got["threshold"]["report_to_author"] is True
    assert L.threshold_report(L.projection(s), 39.99)["reached"] == []


def test_review_m3_seal_reports_the_threshold(ada_repo, tmp_path, capsys):
    ps, job = _launched(ada_repo, tmp_path, hours=41.0)
    L.seal(job, ps, "kev-0.8b", tmp_path / "sealed")
    got = L.seal_threshold(ps, tmp_path / "sealed")
    assert got["gpu_hours"] == 41.0 and got["report_to_author"] is True
    assert "REPORT TO THE AUTHOR" in capsys.readouterr().err


def test_review_m4_an_attempt_logging_a_direct_class_is_not_sealed_as_htcondor(ada_repo, tmp_path):
    ps, job = _launched(ada_repo, tmp_path)
    (job / L.DIRECT_LAUNCH_FILE).unlink()
    (job / "job_record.json").write_text("")                 # the record lost too: only the wrapper's log tells
    (job / "SHA256SUMS").write_text("")
    (job / "p4_run.log").write_text(f"P4 probe container job start 2026-11-27T00:00:00Z host=x arm=kev-0.8b "
                                    f"host_class={ADA} uid=1000\n")
    with pytest.raises(L.Stop, match="p4_run.log names the direct class ada_rtx6000"):
        L.seal(job, ps, "kev-0.8b", tmp_path / "sealed")
    assert L.logged_host_class(job) == ADA


def test_review_m8_a_shared_card_probe_is_marked_descriptive():
    assert L.card_was_shared({}, {"card_shared": True})
    assert L.card_was_shared({"card_processes_end": {"count": 1}}, {})
    assert not L.card_was_shared({"card_processes_start": {"count": 0}}, {"other_processes_start": {"count": 0}})
