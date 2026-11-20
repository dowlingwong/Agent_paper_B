"""G.4 T1 pilot on NEMO2 H200: spec, projection, pilot file, JDL stage, two-key switch, D14 recompute (synthetic)."""
from __future__ import annotations

import copy
import json
import sys
from datetime import date
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
        for key in ("node_spec_sha256", "deployed_pin_sha256", "run_seconds", "env", "spec_path", "node_dir"):
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
])
def test_spec_refusals(mutate, needle):
    with pytest.raises(g4.Stop, match=needle):
        g4.validate_spec(_mut(mutate))


def test_pilot_file_carries_the_gate_inputs():
    node = SPEC["nodes"][1]
    p = g4.pilot_file(SPEC, node, base_url="http://127.0.0.1:5/v1", interpreter="/e/bin/python",
                      cgroup_parent="/sys/fs/cgroup/j", memory="m")
    assert p["frozen_pin_sha256"] == node["deployed_pin_sha256"] and p["isolation_waivers"] == {}
    assert p["extra_payload"] == {"cache_prompt": False} and p["model"] == "gemma4_31b" and p["budget"] == 20
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


def test_preview_stage_and_launch_stage(tmp_path):
    m = g4.stage(G4 / "g4_spec.json", tmp_path / "p", preview=True)
    text = (tmp_path / "p" / "g4_mlgym_fmnist.jdl").read_text()
    assert m["preview"] and "PREVIEW_NOT_SUBMITTABLE_g4_job.sh" in text and 'GPUs_DeviceName =?= "NVIDIA H200"' in text
    assert "transfer_input_files = g4_job.sh,g4_lib.py,g1b_lib.py,s2_c2_lib.py,g4_spec.json" in text
    for name in g4.STAGED:
        assert (tmp_path / "p" / name).read_bytes() == g4._staged_source(name).read_bytes()


def _note(spec, **over):
    f = {"approved": "true", "label": "ENGINEERING_ONLY", "run_id": spec["run_id"], "image": g4.IMAGE_DIGEST,
         "versions_sha256": spec["image"]["versions_sha256"], "llama_server_sha256": spec["image"]["llama_server_sha256"],
         "harness_commit": spec["harness"]["commit"], "nodes": ",".join(n["node"] for n in spec["nodes"]),
         "budget_per_instance": "20", "instances_per_node": "3", "gpu_hours": "10",
         "P1": "PASS — R1-T1-HOST-H200 host check", "P2": "PASS — R1-TRACKG-G3-EARLY",
         "P3": "PASS — G1B first node record clean", "P4": "PASS — reviewed", "labels_read": "none"}
    f.update(over)
    return "".join(f"{k}: {v}\n" for k, v in f.items())


def test_switch_two_keys_and_refusals(tmp_path, monkeypatch):
    spec = launch_spec()
    sp = tmp_path / "spec.json"
    sp.write_text(json.dumps(spec))
    g4.stage(sp, tmp_path / "stage")
    note = g4.REPO_ROOT / "docs" / "r1" / "authorizations" / "g4_t1_pilot_20991231.md"
    assert not note.exists()
    note.write_text(_note(spec))
    try:
        assert g4.check(tmp_path / "stage", note, on_main=lambda r, b: True)["run_id"] == spec["run_id"]
        with pytest.raises(g4.Stop, match="origin/main"):
            g4.check(tmp_path / "stage", note, on_main=lambda r, b: False)
        monkeypatch.delenv("G4_ENABLE_REAL", raising=False)
        with pytest.raises(g4.Stop, match="disabled"):
            g4.submit(tmp_path / "stage", note, enable=True, on_main=lambda r, b: True)
        note.write_text(_note(spec, nodes="mlab_cifar10,mlgym_fmnist,autoresearch_fixedtokens"))
        with pytest.raises(g4.Stop, match="nodes"):
            g4.check(tmp_path / "stage", note, on_main=lambda r, b: True)
        note.write_text(_note(spec, gpu_hours="2"))
        with pytest.raises(g4.Stop, match="more GPU-hours"):
            g4.check(tmp_path / "stage", note, on_main=lambda r, b: True)
    finally:
        note.unlink()  # this test's own temporary note
    for over, needle in (({"approved": "false"}, "approved"), ({"gpu_hours": "25"}, "gpu_hours"),
                         ({"P3": "PASS — other"}, "cite")):
        with pytest.raises(g4.Stop, match=needle):
            g4.parse_note(_note(spec, **over))


def _summary(node, llm, ran, valid):
    return {"node": node, "seconds": {"llm_median": llm}, "diff_liveness": {"ran_of_valid": ran, "valid_of_proposals": valid}}


def test_dates_recompute_arithmetic():
    params = json.loads((G4 / "g4_dates_params.json").read_text())
    sums = {"mlab_cifar10": _summary("mlab_cifar10", 40.0, 0.8, 0.9), "mlgym_fmnist": _summary("mlgym_fmnist", 50.0, 0.7, 0.9)}
    out = g4.recompute_dates(sums, params, today=date(2026, 11, 21))
    share = (0.8 * 0.9 + 0.7 * 0.9) / 2
    assert out["inputs"]["executed_share"] == pytest.approx(share) and out["inputs"]["llm_seconds_median"] == 45.0
    cifar = out["g5_per_node"]["mlab_cifar10"]
    proposals = -(-150 // share) if share else None
    assert cifar["proposals"] == int(proposals)
    want = (cifar["proposals"] * (45.0 + 12.297 * share) + 150 * 6 * 12.297) / 3600
    assert cifar["gpu_hours"] == pytest.approx(want, abs=0.01)
    k10 = g4.recompute_dates(sums, dict(params, audit_seeds_K=10), today=date(2026, 11, 21))
    assert k10["g5_total_gpu_hours"] > out["g5_total_gpu_hours"]
    assert out["targets_R1_BX_D14"]["B7"] == "2026-12-08"
    assert date.fromisoformat(out["B7"]) - date.fromisoformat(out["labels_done"]) == \
        __import__("datetime").timedelta(days=params["analysis_days_to_b7"])
