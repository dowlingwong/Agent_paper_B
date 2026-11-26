"""G.4 T1 pilot on NEMO2 H200: spec, projection, pilot file, JDL stage, two-key switch, D14 recompute (synthetic)."""
from __future__ import annotations

import copy
import math
import hashlib
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
G4 = ROOT / "sweep2" / "g4"
sys.path.insert(0, str(G4))
import g4_lib as g4  # noqa: E402

SPEC = json.loads((G4 / "g4_spec.json").read_text())
G1B_SPEC = json.loads((ROOT / "sweep2" / "g1b" / "g1b_spec.json").read_text())


def launch_spec() -> dict:
    spec = copy.deepcopy(SPEC)
    spec["image"]["versions_sha256"] = "1" * 64
    spec["image"]["llama_server_sha256"] = "2" * 64
    spec["paper"]["commit"] = "3" * 40
    return spec


def test_spec_validates_and_projects_under_the_pilot_cap():
    proj = g4.validate_spec(copy.deepcopy(SPEC))["projection"]
    assert proj["proposals_total"] == 3 * 3 * 20 and proj["total_gpu_hours"] < g4.CAP_PILOT_GPU_HOURS
    assert proj["per_node"]["mlab_cifar10"]["campaign_steps"] == 63
    with pytest.raises(g4.Stop, match="versions_sha256"):
        g4.validate_spec(copy.deepcopy(SPEC), launch=True)
    g4.validate_spec(launch_spec(), launch=True)


def test_node_pins_equal_the_g1b_spec():
    by = {n["node"]: n for n in G1B_SPEC["nodes"]}
    for node in SPEC["nodes"]:
        for key in ("node_spec_sha256", "committed_pin_sha256", "data_manifest_sha256", "run_seconds", "env",
                    "spec_path", "node_dir"):
            assert node[key] == by[node["node"]][key], (node["node"], key)
    assert SPEC["envs"] == G1B_SPEC["envs"] and SPEC["harness"]["commit"] == G1B_SPEC["harness"]["commit"]


def _mut(fn):
    spec = copy.deepcopy(SPEC)
    fn(spec)
    return spec


@pytest.mark.parametrize("mutate, needle", [
    (lambda s: s["nodes"].reverse(), "pilot nodes"),
    (lambda s: s.update(third_node_reason=""), "third_node_reason"),
    (lambda s: s["pilot"]["instances"][0].update(train_seed=7001), "pilot block"),
    (lambda s: s["pilot"]["instances"][1].update(manager_seed=1005), "pilot block"),
    (lambda s: s["pilot"].update(budget=10), "W = 20"),
    (lambda s: s["pilot"].update(cache_prompt=True), "cache_prompt"),
    (lambda s: s["pilot"].update(proposal_schema="manager_proposal/v1"), "v2-diff"),
    (lambda s: s["server"]["extra_args"].remove("--no-webui"), "exam flags"),
    (lambda s: s["server"].update(ctx=16384), "exam flags"),
    (lambda s: s["model"].update(sha256="0" * 64), "gemma4_31b"),
    (lambda s: s["caps"].update(max_total_gpu_hours=40), "caps"),
    (lambda s: s["caps"].update(max_total_gpu_hours=2), "projects"),
    (lambda s: s.update(gpu_model="NVIDIA L40S"), "H200"),
    (lambda s: s["nodes"].pop(), "exactly three"),
    (lambda s: s["nodes"][0].update(committed_pin_sha256="x"), "committed_pin_sha256"),
    (lambda s: s["nodes"][0].pop("data_manifest_sha256"), "data_manifest_sha256"),
    (lambda s: s["nodes"][0].update(data_manifest_sha256="y"), "data_manifest_sha256"),
    (lambda s: s["pilot"].update(max_tokens=10 ** 9), "completion cap"),
    (lambda s: s["pilot"].update(max_tokens="lots"), "completion cap"),
    (lambda s: s["pilot"].update(temperature=0.0), "temperature"),
    (lambda s: s["pilot"].update(memory_mode="append_only_summary"), "memory_mode"),
    (lambda s: s["pilot"]["instances"][0].update(extra=1), "exactly train_seed"),
    (lambda s: s["pilot"]["instances"].__setitem__(1, dict(s["pilot"]["instances"][0])), "distinct seed triples"),
    (lambda s: s["nodes"][0].update(node_dir="../x"), "relative path"),
    (lambda s: s["nodes"][0].update(spec_path="/abs.yaml"), "relative path"),
    (lambda s: s["nodes"][0].update(run_seconds=13.0), "differs from g1b_spec"),
    (lambda s: s["harness"].update(commit="9" * 40), "harness.commit must equal"),
    (lambda s: s["envs"]["torch312"].update(sha256="0" * 64), "envs and harness.commit"),
    (lambda s: s["caps"].update(max_total_gpu_hours=7.0), "slot-h"),
])
def test_spec_refusals(mutate, needle):
    with pytest.raises(g4.Stop, match=needle):
        g4.validate_spec(_mut(mutate))


def test_pilot_file_carries_the_gate_inputs():
    node = SPEC["nodes"][1]
    p = g4.pilot_file(SPEC, node, base_url="http://127.0.0.1:5/v1", interpreter="/e/bin/python",
                      cgroup_parent="/sys/fs/cgroup/j", memory="m")
    assert p["committed_pin_sha256"] == node["committed_pin_sha256"] and p["isolation_waivers"] == {}
    assert p["data_manifest_sha256"] == node["data_manifest_sha256"] and "frozen_pin_sha256" not in p
    assert p["extra_payload"] == {"cache_prompt": False} and p["model"] == "gemma4_31b" and p["budget"] == 20
    assert p["max_tokens"] == 4096 and p["temperature"] == 0.2 and p["memory_mode"] == "history"
    assert [i["instance"] for i in p["instances"]] == [1, 2, 3] and p["instances"][0]["train_seed"] == 4001


def test_job_stops_as_root_and_writes_outputs(tmp_path, monkeypatch):
    path = tmp_path / "g4_spec.json"
    path.write_text(json.dumps(launch_spec()))
    monkeypatch.setenv("_CONDOR_SCRATCH_DIR", str(tmp_path))
    monkeypatch.setattr(g4.g1b_lib, "image_identity", lambda s: {"digest": s["image"]["digest"]})
    monkeypatch.setattr(g4, "llama_identity", lambda s: {})
    monkeypatch.setattr(g4.g1b_lib, "host_identity", lambda: {"euid": 0})
    with pytest.raises(g4.Stop, match="root"):
        g4.run_node_job(path, "mlab_cifar10")
    rec = json.loads((tmp_path / "job_record.json").read_text())
    assert "root" in rec["stop"] and (tmp_path / "SHA256SUMS").is_file() and (tmp_path / "out.tar").is_file()


def test_job_stop_at_validation_still_writes_a_record(tmp_path, monkeypatch):
    path = tmp_path / "g4_spec.json"
    path.write_text(json.dumps(copy.deepcopy(SPEC)))
    monkeypatch.setenv("_CONDOR_SCRATCH_DIR", str(tmp_path))
    with pytest.raises(g4.Stop, match="versions_sha256"):
        g4.run_node_job(path, "mlab_cifar10")
    rec = json.loads((tmp_path / "job_record.json").read_text())
    assert "versions_sha256" in rec["stop"] and rec["spec_sha256"] == g4.g1b_lib._sha_file(path)
    assert "job_record.json" in (tmp_path / "SHA256SUMS").read_text()


def test_preview_stage_and_launch_stage(tmp_path):
    m = g4.stage(G4 / "g4_spec.json", tmp_path / "p", preview=True)
    text = (tmp_path / "p" / "g4_mlgym_fmnist.jdl").read_text()
    assert m["preview"] and "PREVIEW_NOT_SUBMITTABLE_g4_job.sh" in text and 'GPUs_DeviceName =?= "NVIDIA H200"' in text
    assert "transfer_input_files = g4_job.sh,g4_lib.py,g1b_lib.py,s2_c2_lib.py,g4_spec.json" in text
    for name in g4.STAGED:
        assert (tmp_path / "p" / name).read_bytes() == g4._staged_source(name).read_bytes()


def _note(spec, receipt=None, **over):
    f = {"approved": "true", "label": "ENGINEERING_ONLY", "run_id": spec["run_id"], "image": g4.IMAGE_DIGEST,
         "versions_sha256": spec["image"]["versions_sha256"], "llama_server_sha256": spec["image"]["llama_server_sha256"],
         "harness_commit": spec["harness"]["commit"], "nodes": ",".join(n["node"] for n in spec["nodes"]),
         "paper_commit": spec["paper"]["commit"], "spec_sha256": hashlib.sha256(json.dumps(spec).encode()).hexdigest(),
         "budget_per_instance": "20", "instances_per_node": "3", "gpu_hours": "10",
         "P1": "PASS — R1-T1-HOST-H200 host check", "P2": "PASS — R1-TRACKG-G3-EARLY",
         "P3": f"PASS — G1B first node g1b_first_receipt={receipt[0]} sha256={receipt[1]}" if receipt else
         "PASS — G1B first node record clean",
         "P4": "PASS — docs/r1/reviews/G4_H200_REVIEW.md", "P5": "PASS — R1-T1-IMAGE-V2: test row",
         "labels_read": "none"}
    f.update(over)
    return "".join(f"{k}: {v}\n" for k, v in f.items())


def _receipt(tmp_path, stop_class=None, **record_over):
    """A sealed G.1b first-node directory under a temporary SEALED_ROOT (the fixture sets it)."""
    spec = launch_spec()
    d = g4.g1b_lib.SEALED_ROOT / "g1b_run" / g4.G1B_FIRST_NODE
    d.mkdir(parents=True, exist_ok=True)
    record = {"node": g4.G1B_FIRST_NODE, "image": {"digest": g4.IMAGE_DIGEST}, "harness_commit": spec["harness"]["commit"]}
    record.update(record_over)
    (d / "job_record.json").write_text(json.dumps(record))
    (d / "out.tar").write_bytes(b"tar")
    g4.g1b_lib._write_sums(d, ("out.tar", "job_record.json"))
    path = d / "SEAL_RECEIPT.json"
    path.write_text(json.dumps({"schema": "g1b_h200_seal_receipt/1", "stop_class": stop_class,
                                "node": g4.G1B_FIRST_NODE,
                                "job_record_sha256": g4.g1b_lib._sha_file(d / "job_record.json")}))
    return str(path), g4.g1b_lib._sha_file(path)


@pytest.fixture
def staged(tmp_path, monkeypatch):
    """A launch stage and a temporary repository root for the note (the checkout's docs are never written)."""
    spec = launch_spec()
    sp = tmp_path / "spec.json"
    sp.write_text(json.dumps(spec))
    g4.stage(sp, tmp_path / "stage")
    root = tmp_path / "repo"
    (root / "docs" / "r1" / "authorizations").mkdir(parents=True)
    monkeypatch.setattr(g4, "REPO_ROOT", root)
    monkeypatch.setattr(g4.g1b_lib, "SEALED_ROOT", tmp_path / "g1b_sealed")
    return spec, tmp_path / "stage", root / "docs" / "r1" / "authorizations" / "g4_t1_pilot_20991231.md"


def test_switch_two_keys_and_refusals(staged, tmp_path, monkeypatch):
    spec, stage, note = staged
    rec = _receipt(tmp_path)
    note.write_text(_note(spec, rec))
    yes = lambda r, b: True  # noqa: E731
    assert g4.check(stage, note, on_main=yes)["run_id"] == spec["run_id"]
    with pytest.raises(g4.Stop, match="origin/main"):
        g4.check(stage, note, on_main=lambda r, b: False)
    monkeypatch.delenv("G4_ENABLE_REAL", raising=False)
    with pytest.raises(g4.Stop, match="disabled"):
        g4.submit(stage, note, enable=True, on_main=yes)
    monkeypatch.setenv("G4_ENABLE_REAL", "1")
    with pytest.raises(g4.Stop, match="disabled"):
        g4.submit(stage, note, enable=False, on_main=yes)

    def refuse(repo, spec_, rows):
        assert rows == g4.PLAN_ROWS + ("R1-T1-IMAGE-V2",)
        raise g4.Stop("STOP: fetch published main before launch")
    with pytest.raises(g4.Stop, match="fetch published main"):
        g4.submit(stage, note, enable=True, on_main=yes, launch_binding=refuse)
    assert not list(stage.glob("G4_SUBMIT_STARTED_*"))
    calls = []
    monkeypatch.setattr(g4.subprocess, "run", lambda argv, **k: calls.append(argv) or
                        type("R", (), {"returncode": 0, "stdout": "1 job(s) submitted", "stderr": ""})())
    seen = []
    with pytest.raises(g4.Stop, match="P5 image"):
        g4.submit(stage, note, enable=True, node="mlab_cifar10", on_main=yes, launch_binding=lambda *a: {},
                  row_check=lambda row, repo, terms, what: (_ for _ in ()).throw(g4.Stop(f"STOP: the {what} row")))
    assert not [c for c in calls if c[0] == "condor_submit"]
    rows_checked = []
    out = g4.submit(stage, note, enable=True, node="mlab_cifar10", on_main=yes,
                    launch_binding=lambda repo, sp, rows: seen.append(rows) or {},
                    row_check=lambda row, repo, terms, what: rows_checked.append((row, terms)))
    assert seen == [g4.PLAN_ROWS + ("R1-T1-IMAGE-V2",)]
    assert rows_checked == [("R1-T1-IMAGE-V2", g4.IMAGE_ROW_TERMS)]
    assert [c for c in calls if c[0] == "condor_submit"] == [["condor_submit", "g4_mlab_cifar10.jdl"]]
    assert len(out["submitted"]) == 1
    with pytest.raises(g4.Stop, match="already submitted"):
        g4.submit(stage, note, enable=True, node="mlab_cifar10", on_main=yes, launch_binding=lambda *a: {},
                  row_check=lambda *a, **k: None)
    with pytest.raises(g4.Stop, match="not an authorized"):
        g4.submit(stage, note, enable=True, node="mlab_imdb", on_main=yes, launch_binding=lambda *a: {},
                  row_check=lambda *a, **k: None)


def test_switch_binds_note_fields_and_the_g1b_receipt(staged, tmp_path):
    spec, stage, note = staged
    rec = _receipt(tmp_path)
    yes = lambda r, b: True  # noqa: E731
    for key, bad, match in (("paper_commit", "4" * 40, "paper_commit"), ("spec_sha256", "5" * 64, "spec_sha256"),
                            ("nodes", "mlab_cifar10,mlgym_fmnist,autoresearch_fixedtokens", "nodes"),
                            ("gpu_hours", "2", "more GPU-hours")):
        note.write_text(_note(spec, rec, **{key: bad}))
        with pytest.raises(g4.Stop, match=match):
            g4.check(stage, note, on_main=yes)
    note.write_text(_note(spec))
    with pytest.raises(g4.Stop, match="g1b_first_receipt"):
        g4.check(stage, note, on_main=yes)
    note.write_text(_note(spec, (rec[0], "0" * 64)))
    with pytest.raises(g4.Stop, match="sha256 differs"):
        g4.check(stage, note, on_main=yes)
    for kwargs, problem in (({"stop_class": "infrastructure"}, "stop_class"), ({"node": "mlab_imdb"}, "node"),
                            ({"image": {"digest": "x"}}, "image"), ({"harness_commit": "0" * 40}, "harness")):
        bad = _receipt(tmp_path, **kwargs)
        note.write_text(_note(spec, bad))
        with pytest.raises(g4.Stop, match=problem):
            g4.check(stage, note, on_main=yes)
    good = _receipt(tmp_path)
    (Path(good[0]).parent / "out.tar").write_bytes(b"changed")
    note.write_text(_note(spec, (good[0], g4.g1b_lib._sha_file(good[0]))))
    with pytest.raises(g4.Stop, match="sums"):
        g4.check(stage, note, on_main=yes)
    elsewhere = tmp_path / "elsewhere" / g4.G1B_FIRST_NODE
    elsewhere.mkdir(parents=True)
    copy_path = elsewhere / "SEAL_RECEIPT.json"
    copy_path.write_text(Path(_receipt(tmp_path)[0]).read_text())
    note.write_text(_note(spec, (str(copy_path), g4.g1b_lib._sha_file(copy_path))))
    with pytest.raises(g4.Stop, match="name"):
        g4.check(stage, note, on_main=yes)


@pytest.mark.parametrize("tamper, match", [
    (lambda st: (st / "g4_lib.py").write_text((st / "g4_lib.py").read_text() + "#\n"), "changed after staging"),
    (lambda st: (st / "g4_mlab_cifar10.jdl").write_text((st / "g4_mlab_cifar10.jdl").read_text()
                                                         .replace("request_GPUs = 1", "request_GPUs = 2")),
     "changed after staging"),
    (lambda st: (st / "STAGE_MANIFEST.json").write_text(
        (st / "STAGE_MANIFEST.json").read_text().replace('"preview": false', '"preview": true')), "preview"),
])
def test_switch_refuses_a_tampered_stage(staged, tmp_path, tamper, match):
    spec, stage, note = staged
    note.write_text(_note(spec, _receipt(tmp_path)))
    tamper(stage)
    with pytest.raises(g4.Stop, match=match):
        g4.check(stage, note, on_main=lambda r, b: True)


def test_switch_refuses_a_stage_that_differs_from_the_checkout(staged, tmp_path, monkeypatch):
    spec, stage, note = staged
    note.write_text(_note(spec, _receipt(tmp_path)))
    real = g4._staged_source
    alt = tmp_path / "alt_g4_job.sh"
    alt.write_text("#!/bin/bash\n")
    monkeypatch.setattr(g4, "_staged_source", lambda name: alt if name == "g4_job.sh" else real(name))
    with pytest.raises(g4.Stop, match="differs from the reviewed checkout"):
        g4.check(stage, note, on_main=lambda r, b: True)


def test_note_refusals():
    spec = launch_spec()
    for over, needle in (({"approved": "false"}, "approved"), ({"gpu_hours": "25"}, "gpu_hours"),
                         ({"P3": "PASS — other"}, "cite"), ({"P5": "pending"}, "PASS"),
                         ({"P4": "PASS — reviewed"}, "cite"), ({"labels_read": "some"}, "labels_read"),
                         ({"P5": "PASS — see R1-T1-IMAGE-V2"}, "row id"), ({"P5": "PASS — R1-SWEEP2-IMAGE"},
                                                                          "does not authorize"),
                         ({"P5": "PASS — R1-T1-HOST-H200"}, "does not authorize")):
        with pytest.raises(g4.Stop, match=needle):
            g4.parse_note(_note(spec, **over))


def test_jdl_holds_on_a_restart(tmp_path):
    text = g4.render(launch_spec(), launch_spec()["nodes"][0])
    assert "periodic_hold = (NumJobStarts > 1)" in text and "when_to_transfer_output = ON_EXIT_OR_EVICT" in text


# ---------------------------------------------------------------------------------------------- job: liveness STOP
def _fake_job(monkeypatch, tmp_path, summary: dict, rc: int = 0):
    path = tmp_path / "g4_spec.json"
    path.write_text(json.dumps(launch_spec()))
    monkeypatch.setenv("_CONDOR_SCRATCH_DIR", str(tmp_path))
    lib = g4.g1b_lib
    monkeypatch.setattr(lib, "image_identity", lambda s: {"digest": g4.IMAGE_DIGEST})
    monkeypatch.setattr(g4, "llama_identity", lambda s: {})
    monkeypatch.setattr(lib, "host_identity", lambda: {"euid": 1000})
    monkeypatch.setattr(lib, "gpu_identity", lambda: {"name": g4.GPU_MODEL})
    monkeypatch.setattr(lib, "clone_at", lambda repo, commit, dest: {"commit": commit})
    staged_calls = []
    monkeypatch.setattr(lib, "check_staged_identity", lambda d, files: staged_calls.append(files))
    monkeypatch.setattr(lib, "build_env", lambda *a: {"freeze_sha256": "x"})
    monkeypatch.setattr(lib, "run_setup", lambda *a: {"setup": None})
    monkeypatch.setattr(lib, "delegated_cgroup", lambda: "/sys/fs/cgroup/job")
    monkeypatch.setattr(g4.s2_c2_lib, "fetch_model", lambda *a: {"sha256": "m"})
    monkeypatch.setattr(g4.s2_c2_lib, "start_server", lambda *a: {"base_url": "http://127.0.0.1:9/v1", "proc": None})
    monkeypatch.setattr(g4.s2_c2_lib, "_kill", lambda proc: None)
    real_run = g4.subprocess.run

    def fake_run(argv, **kw):
        if argv[:3] == [str(tmp_path / "env" / "bin" / "python"), "-m", "autoresearch.trackg.pilot_g4"]:
            out = Path(argv[argv.index("--out") + 1])
            out.mkdir(parents=True)
            (out / "pilot_summary.json").write_text(json.dumps(summary))
            return type("R", (), {"returncode": rc, "stdout": "", "stderr": ""})()
        return real_run(argv, **kw)
    monkeypatch.setattr(g4.subprocess, "run", fake_run)
    return path, staged_calls


def test_zero_liveness_is_a_node_stop_with_a_record(tmp_path, monkeypatch):
    path, staged_calls = _fake_job(monkeypatch, tmp_path, {"diff_liveness": {"ran_of_valid": 0.0}})
    with pytest.raises(g4.Stop, match="diff liveness 0"):
        g4.run_node_job(path, "mlab_cifar10")
    rec = json.loads((tmp_path / "job_record.json").read_text())
    assert rec["stop_class"] == "node" and rec["cgroup_parent"] == "/sys/fs/cgroup/job" and rec["walltime_s"] > 0
    assert staged_calls and "g4_job.sh" in staged_calls[0]
    assert (tmp_path / "SHA256SUMS").is_file() and (tmp_path / "out.tar").is_file()


def test_engine_stop_is_an_infrastructure_stop(tmp_path, monkeypatch):
    path, _ = _fake_job(monkeypatch, tmp_path, {"diff_liveness": {"ran_of_valid": 0.5}}, rc=3)
    with pytest.raises(g4.Stop, match="exited 3"):
        g4.run_node_job(path, "mlab_cifar10")
    assert json.loads((tmp_path / "job_record.json").read_text())["stop_class"] == "infrastructure"


def test_unexpected_exception_still_writes_the_record(tmp_path, monkeypatch):
    path, _ = _fake_job(monkeypatch, tmp_path, {})
    monkeypatch.setattr(g4.g1b_lib, "delegated_cgroup", lambda: (_ for _ in ()).throw(AttributeError("boom")))
    with pytest.raises(g4.Stop, match="AttributeError"):
        g4.run_node_job(path, "mlab_cifar10")
    assert "AttributeError" in json.loads((tmp_path / "job_record.json").read_text())["stop"]


# ---------------------------------------------------------------------------------------------- seal + recompute
def _summary(node, *, llm=40.0, run=10.0, wall=3600.0, ran=0.6, kept=0.25, proposals=60, **over):
    s = {"node": node, "pilot_stop": None, "stops": [], "proposals": proposals,
         "seconds": {"llm_median": llm, "run_median": run, "campaign_wall_total": wall},
         "rates": {"ran_of_proposals": ran, "kept_of_ran": kept}, "diff_liveness": {"ran_of_valid": 0.8}}
    s.update(over)
    return s


PARAMS = json.loads((G4 / "g4_dates_params.json").read_text())


def test_g5_node_formula():
    got = g4.g5_node(run_s=10.0, per_call_s=50.0, ran_share=0.5, keep_share=0.2, k=10, w_semantics="manager_calls",
                     dup_factor=1.0, audit_inflation=1.25, startup_s=1500.0, walltime_limit_s=86400)
    assert got["manager_calls"] == 240 and got["ran"] == 120 and got["audited"] == 120 and got["parents"] == 12
    audit_s = (120 + 12) * 10 * 10.0 * 1.25
    assert got["audit_gpu_hours"] == round(audit_s / 3600, 2) and got["audit_chunks"] == 1 and got["jobs"] == 3
    assert got["gpu_hours"] == round((240 * 50.0 + audit_s + 3 * 1500) / 3600, 2)
    b = g4.g5_node(run_s=10.0, per_call_s=50.0, ran_share=0.5, keep_share=0.2, k=10, w_semantics="worker_runs",
                   dup_factor=1.0, audit_inflation=1.25, startup_s=1500.0, walltime_limit_s=86400)
    assert b["manager_calls"] == 480 and b["ran"] == 240
    capped = g4.g5_node(run_s=10.0, per_call_s=50.0, ran_share=0.1, keep_share=0.2, k=10, w_semantics="worker_runs",
                        dup_factor=1.0, audit_inflation=1.25, startup_s=1500.0, walltime_limit_s=86400)
    assert capped["manager_calls"] == 12 * 80 and capped["ran"] == pytest.approx(96)
    with pytest.raises(g4.Stop, match="W semantics"):
        g4.g5_node(run_s=1, per_call_s=1, ran_share=1, keep_share=0, k=6, w_semantics="x", dup_factor=1,
                   audit_inflation=1, startup_s=0, walltime_limit_s=86400)


def test_recompute_uses_measured_h200_inputs_and_k10_binds():
    sums = {"mlab_cifar10": _summary("mlab_cifar10", run=6.0, wall=60 * 30.0),
            "mlgym_fmnist": _summary("mlgym_fmnist", run=17.0, wall=60 * 50.0)}
    out = g4.recompute_dates(sums, PARAMS, today=date(2026, 11, 21))
    assert out["binding_K"] == 10 and out["g5_total_gpu_hours"] == out["g5_by_K"]["10"]["total_gpu_hours"]
    assert out["g5_by_K"]["6"]["total_gpu_hours"] < out["g5_by_K"]["10"]["total_gpu_hours"]
    cif = out["g5_by_K"]["10"]["per_node"]["mlab_cifar10"]
    assert cif["inputs"]["source"] == "pilot" and cif["inputs"]["per_call_s"] == 30.0 and cif["inputs"]["run_s"] == 6.0
    ratio = (6.0 / 12.297 + 17.0 / 34.376) / 2
    assert out["h200_over_census_run_ratio"] == round(ratio, 4)
    imdb = out["g5_by_K"]["10"]["per_node"]["mlab_imdb"]
    assert imdb["inputs"]["source"] == "census x ratio" and imdb["inputs"]["run_s"] == pytest.approx(64.142 * ratio, 1e-3)
    assert out["today"] == "2026-11-21" and set(out["slack_days"]) == {"B7", "D3", "manuscript"}
    assert out["g5_within_cap"] == (out["g5_total_gpu_hours"] <= PARAMS["g5_cap_gpu_hours"])
    k6 = g4.recompute_dates(sums, dict(PARAMS, k_check_passed=True, k_check_row="R1-BX-D3-KCHECK"),
                            today=date(2026, 11, 21))
    assert k6["binding_K"] == 6 and k6["g5_total_gpu_hours"] < out["g5_total_gpu_hours"]
    assert date.fromisoformat(out["B7"]) - date.fromisoformat(out["labels_done"]) == \
        __import__("datetime").timedelta(days=PARAMS["analysis_days_to_b7"])


@pytest.mark.parametrize("bad, match", [
    ({"pilot_stop": "STOP: x"}, "stopped"), ({"stops": ["stop_transport"]}, "stopped"),
    ({"proposals": 59}, "proposals"), ({"seconds": {"llm_median": None, "run_median": 1, "campaign_wall_total": 1}},
                                       "llm_median"),
    ({"seconds": {"llm_median": 1, "run_median": 0, "campaign_wall_total": 1}}, "run_median"),
    ({"rates": {"ran_of_proposals": None, "kept_of_ran": 0.1}}, "ran_of_proposals"),
    ({"rates": {"ran_of_proposals": 1.5, "kept_of_ran": 0.1}}, "ran_of_proposals"),
    ({"rates": {"ran_of_proposals": 0.0, "kept_of_ran": 0.1}}, "zero diff liveness"),
    ({"rates": {"ran_of_proposals": 0.5, "kept_of_ran": -0.1}}, "kept_of_ran"),
])
def test_recompute_refuses_partial_summaries(bad, match):
    with pytest.raises(g4.Stop, match=match):
        g4.recompute_dates({"mlab_cifar10": _summary("mlab_cifar10", **bad)}, PARAMS, today=date(2026, 11, 21))
    with pytest.raises(g4.Stop, match="not a pilot node"):
        g4.recompute_dates({"mlab_imdb": _summary("mlab_imdb")}, PARAMS, today=date(2026, 11, 21))


def test_seal_and_read_sealed_summary(tmp_path):
    import subprocess
    spec = launch_spec()
    spec_path = tmp_path / "g4_spec.json"
    spec_path.write_text(json.dumps(spec))
    job = tmp_path / "job"
    (job / "out" / "pilot").mkdir(parents=True)
    (job / "out" / "pilot" / "pilot_summary.json").write_text(json.dumps(_summary("mlab_cifar10")))
    subprocess.run(["tar", "-cf", "out.tar", "out"], cwd=job, check=True)
    record = {"label": "ENGINEERING_ONLY", "run_id": spec["run_id"], "node": "mlab_cifar10",
              "spec_sha256": g4.g1b_lib._sha_file(spec_path), "harness_commit": spec["harness"]["commit"],
              "image": {"digest": g4.IMAGE_DIGEST}, "gpu": {"name": g4.GPU_MODEL}, "stop": None, "stop_class": None}
    (job / "job_record.json").write_text(json.dumps(record))
    g4.g1b_lib._write_sums(job, ("out.tar", "job_record.json"))
    (job / "g4_run.log").write_text("log\n")
    receipt = g4.seal(job, spec["run_id"], "mlab_cifar10", sealed_root=tmp_path / "sealed")
    assert receipt["g4_run_log_sha256"] and receipt["job_record_sha256"]
    sealed = tmp_path / "sealed" / spec["run_id"] / "mlab_cifar10"
    assert g4.read_sealed_summary(sealed, spec, g4.g1b_lib._sha_file(spec_path))["node"] == "mlab_cifar10"
    with pytest.raises(g4.Stop, match="no overwrite"):
        g4.seal(job, spec["run_id"], "mlab_cifar10", sealed_root=tmp_path / "sealed")
    with pytest.raises(g4.Stop, match="spec_sha256"):
        g4.read_sealed_summary(sealed, spec, "0" * 64)
    with (sealed / "out.tar").open("ab") as fh:
        fh.write(b"\0")
    with pytest.raises(g4.Stop, match="SHA256SUMS"):
        g4.read_sealed_summary(sealed, spec, g4.g1b_lib._sha_file(spec_path))


def test_recompute_k_binding_needs_a_row_and_parents_and_duplicates():
    with pytest.raises(g4.Stop, match="true or false"):
        g4.recompute_dates({}, dict(PARAMS, k_check_passed="no"), today=date(2026, 11, 21))
    with pytest.raises(g4.Stop, match="k_check_row"):
        g4.recompute_dates({}, dict(PARAMS, k_check_passed=True), today=date(2026, 11, 21))
    out = g4.recompute_dates({}, dict(PARAMS, k_check_passed=True, k_check_row="R1-BX-D3-KCHECK"),
                             today=date(2026, 11, 21))
    assert out["binding_K"] == 6 and out["nodes_from_census_x_ratio"] == sorted(PARAMS["t1_nodes"])
    rerun = g4.recompute_dates({}, dict(PARAMS, reuse_parent_runs=False), today=date(2026, 11, 21))
    reuse = g4.recompute_dates({}, PARAMS, today=date(2026, 11, 21))
    assert rerun["g5_total_gpu_hours"] > reuse["g5_total_gpu_hours"]
    both = g4.recompute_dates({}, dict(PARAMS, mem_modes=2), today=date(2026, 11, 21))
    assert both["g5_total_gpu_hours"] == pytest.approx(2 * reuse["g5_total_gpu_hours"], abs=0.2)
    s = _summary("mlab_cifar10", cross_instance_duplicates={"groups": 3, "ran_proposals_in_groups": 9})
    d = g4.recompute_dates({"mlab_cifar10": s}, PARAMS, today=date(2026, 11, 21))
    assert d["dup_factor_used"] == round(1 - (9 - 3) / 36, 4)
    assert d["dup_factor_source"].startswith("pilot") and reuse["dup_factor_source"].startswith("params")
    assert d["g5_requested_slot_hours"] > d["g5_total_gpu_hours"] and d["g5_slot_cap"] == PARAMS["g5_cap_gpu_hours"] * 1.6
    assert d["longest_node_gpu_hours"] > 0 and "census" in d["ratio_basis"]


def test_check_plan_row(tmp_path):
    import subprocess
    repo = tmp_path / "r"
    env = dict(__import__("os").environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@t", GIT_CONFIG_GLOBAL="/dev/null")
    for cmd in (["init", "-q", "-b", "main", str(repo)],):
        subprocess.run(["git", *cmd], check=True, env=env)
    (repo / "docs" / "r1").mkdir(parents=True)
    (repo / "docs" / "r1" / "PLAN.md").write_text(
        "| R1-BX-D3-KCHECK | K-check PASS on T0 |\n| R1-BX-D3-OTHER | something else |\n"
        "| R1-T1-IMAGE-V2 | image b1144ece authorized for the T1 table |\n")
    for cmd in (["add", "-A"], ["commit", "-qm", "x"], ["update-ref", "refs/remotes/origin/main", "HEAD"]):
        subprocess.run(["git", "-C", str(repo), *cmd], check=True, env=env)
    assert "K-check PASS" in g4.check_plan_row("R1-BX-D3-KCHECK", repo)
    with pytest.raises(g4.Stop, match="not on origin/main"):
        g4.check_plan_row("R1-OTHER", repo)
    with pytest.raises(g4.Stop, match="does not name"):
        g4.check_plan_row("R1-BX-D3-OTHER", repo)
    g4.check_plan_row("R1-T1-IMAGE-V2", repo, terms=g4.IMAGE_ROW_TERMS, what="P5 image")
    with pytest.raises(g4.Stop, match="P5 image row 'R1-BX-D3-KCHECK' does not name"):
        g4.check_plan_row("R1-BX-D3-KCHECK", repo, terms=g4.IMAGE_ROW_TERMS, what="P5 image")


def test_job_refuses_cache_and_fit_failures(tmp_path, monkeypatch):
    path, _ = _fake_job(monkeypatch, tmp_path, {"diff_liveness": {"ran_of_valid": 0.5},
                                                "fit": {"cache_prompt_false_on_every_call": False, "all_fit_ctx": True}})
    with pytest.raises(g4.Stop, match="cache_prompt"):
        g4.run_node_job(path, "mlab_cifar10")
    assert json.loads((tmp_path / "job_record.json").read_text())["stop_class"] == "infrastructure"


def test_job_refuses_a_prompt_over_the_context(tmp_path, monkeypatch):
    path, _ = _fake_job(monkeypatch, tmp_path, {"diff_liveness": {"ran_of_valid": 0.5},
                                                "fit": {"cache_prompt_false_on_every_call": True, "all_fit_ctx": False}})
    with pytest.raises(g4.Stop, match="context"):
        g4.run_node_job(path, "mlab_cifar10")
    assert json.loads((tmp_path / "job_record.json").read_text())["stop_class"] == "node"


def _sealed_g4(tmp_path, spec, spec_path, *, record_over=None, summary=None, with_summary=True):
    import subprocess
    job = tmp_path / "job"
    (job / "out" / "pilot").mkdir(parents=True)
    if with_summary:
        (job / "out" / "pilot" / "pilot_summary.json").write_text(json.dumps(summary or _summary("mlab_cifar10")))
    subprocess.run(["tar", "-cf", "out.tar", "out"], cwd=job, check=True)
    record = {"label": "ENGINEERING_ONLY", "run_id": spec["run_id"], "node": "mlab_cifar10",
              "spec_sha256": g4.g1b_lib._sha_file(spec_path), "harness_commit": spec["harness"]["commit"],
              "image": {"digest": g4.IMAGE_DIGEST}, "gpu": {"name": g4.GPU_MODEL}, "stop": None, "stop_class": None}
    record.update(record_over or {})
    (job / "job_record.json").write_text(json.dumps(record))
    g4.g1b_lib._write_sums(job, ("out.tar", "job_record.json"))
    return job


def test_seal_refuses_bad_sums_and_read_refuses_bad_receipts(tmp_path):
    spec = launch_spec()
    spec_path = tmp_path / "g4_spec.json"
    spec_path.write_text(json.dumps(spec))
    job = _sealed_g4(tmp_path, spec, spec_path)
    with (job / "out.tar").open("ab") as fh:
        fh.write(b"\0")
    with pytest.raises(g4.Stop, match="SHA256SUMS"):
        g4.seal(job, spec["run_id"], "mlab_cifar10", sealed_root=tmp_path / "s0")
    for i, (over, match) in enumerate(((({"stop": "STOP: diff liveness 0"}), "stop"),
                                       ({"harness_commit": "0" * 40}, "harness_commit"))):
        sub = tmp_path / f"c{i}"
        sub.mkdir()
        j = _sealed_g4(sub, spec, spec_path, record_over=over)
        g4.seal(j, spec["run_id"], "mlab_cifar10", sealed_root=sub / "sealed")
        with pytest.raises(g4.Stop, match=match):
            g4.read_sealed_summary(sub / "sealed" / spec["run_id"] / "mlab_cifar10", spec,
                                   g4.g1b_lib._sha_file(spec_path))
    sub = tmp_path / "r"
    sub.mkdir()
    j = _sealed_g4(sub, spec, spec_path)
    g4.seal(j, spec["run_id"], "mlab_cifar10", sealed_root=sub / "sealed")
    sealed = sub / "sealed" / spec["run_id"] / "mlab_cifar10"
    receipt = json.loads((sealed / "SEAL_RECEIPT.json").read_text())
    (sealed / "SEAL_RECEIPT.json").write_text(json.dumps(dict(receipt, job_record_sha256="0" * 64)))
    with pytest.raises(g4.Stop, match="receipt"):
        g4.read_sealed_summary(sealed, spec, g4.g1b_lib._sha_file(spec_path))
    sub = tmp_path / "n"
    sub.mkdir()
    j = _sealed_g4(sub, spec, spec_path, with_summary=False)
    g4.seal(j, spec["run_id"], "mlab_cifar10", sealed_root=sub / "sealed")
    with pytest.raises(g4.Stop, match="no out/pilot/pilot_summary.json"):
        g4.read_sealed_summary(sub / "sealed" / spec["run_id"] / "mlab_cifar10", spec, g4.g1b_lib._sha_file(spec_path))


def test_switch_refuses_a_g1b_receipt_that_does_not_bind_the_record(staged, tmp_path):
    spec, stage, note = staged
    path, _ = _receipt(tmp_path)
    d = Path(path).parent
    record = json.loads((d / "job_record.json").read_text())
    record["extra"] = "changed after sealing"
    (d / "job_record.json").write_text(json.dumps(record))
    g4.g1b_lib._write_sums(d, ("out.tar", "job_record.json"))       # the sums agree; only the receipt binding fails
    note.write_text(_note(spec, (path, g4.g1b_lib._sha_file(path))))
    with pytest.raises(g4.Stop, match=r"\['record'\]"):
        g4.check(stage, note, on_main=lambda r, b: True)


def test_recompute_refuses_mem_modes_outside_one_or_two():
    for bad in (0, 3):
        with pytest.raises(g4.Stop, match="mem_modes"):
            g4.recompute_dates({}, dict(PARAMS, mem_modes=bad), today=date(2026, 11, 21))


def test_label_span_is_at_least_the_longest_node():
    sums = {"mlab_cifar10": _summary("mlab_cifar10", run=600.0, wall=60 * 30.0)}
    many = dict(PARAMS, concurrent_h200_slots=10_000)
    out = g4.recompute_dates(sums, many, today=date(2026, 11, 21))
    longest = out["longest_node_gpu_hours"]
    assert longest > out["g5_total_gpu_hours"] / 10_000
    days = math.ceil(float(many["prerequisite_days"]) + float(many.get("g1b_days", 0)) + float(many["queue_days"])
                     + longest / 24.0)
    assert out["labels_done"] == (date(2026, 11, 21) + timedelta(days=days)).isoformat()


def test_cli_dates_checks_the_k_check_row(tmp_path, monkeypatch, capsys):
    p = tmp_path / "params.json"
    p.write_text(json.dumps(dict(PARAMS, k_check_passed=True, k_check_row="R1-BX-D3-KCHECK")))
    seen = []
    monkeypatch.setattr(g4, "check_plan_row", lambda row, *a, **k: seen.append(row) or "")
    assert g4.main(["dates", "--params", str(p), "--today", "2026-11-21"]) == 0
    assert seen == ["R1-BX-D3-KCHECK"] and json.loads(capsys.readouterr().out)["binding_K"] == 6

    def refuse(row, *a, **k):
        raise g4.Stop(f"STOP: the K-check row {row!r} is not on origin/main PLAN")
    monkeypatch.setattr(g4, "check_plan_row", refuse)
    assert g4.main(["dates", "--params", str(p), "--today", "2026-11-21"]) == 2
    assert "not on origin/main" in capsys.readouterr().err
    p.write_text(json.dumps(PARAMS))                               # K-check not passed: no row is consulted
    assert g4.main(["dates", "--params", str(p), "--today", "2026-11-21"]) == 0
