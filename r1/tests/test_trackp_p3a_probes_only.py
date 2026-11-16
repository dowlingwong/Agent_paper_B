"""CPU-only tests for the P.3a attempt-2 probes-only runner (Unit A plan §1c.2).

No GPU, no model, no host: the TASL-7 preflight, marker helper and child units are stubbed, and the attempt-1 root
is a synthetic temp tree. The tests pin the fail-closed argument contract, the budget projection arithmetic, the
attempt-1 provenance/hash walk, the M13 template block and the exact two-command DRYRUN/EVIDENCE sequence.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from r1.scripts import trackp_p3a_guarded as G

KEV_COMMIT = "2074cc44256200bb37540103fa4572901faa10f3"
A1_BASES = {"kev-0.8b": "kev", "qwen3.5-4b-base": "qwen_control"}


def _write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def _saved_describe(family: str) -> dict:
    out = {"family": family, "model_version": "trackp_model/v1", "head_form": "linear12", "action_head": True}
    if family == "kev":
        out.update({"kev_hybrid": True, "pointer_temperature": 1.0, "released_temperature": 2.35})
    else:
        out.update({"list_bins": True, "bin_order": list(range(12))})
    return out


def _attempt1_final_manifest(base: str, family: str) -> dict:
    return {"schema": "trackp_run_manifest/v1", "subcommand": "e0-final",
            "base": {"family": family, "base_repo": f"Repo/{base}", "base_revision": "abc123"},
            "environment": {"transformers": "5.19.0", "torch": "2.6.0+cu124",
                            "packages": {"kev": {"pip_commit": KEV_COMMIT}}},
            "evidence_label": "EVIDENCE"}


def make_attempt1_root(tmp_path: Path, *, gpu_seconds: float = G.ATTEMPT1_GPU_SECONDS_TOTAL,
                       paper_commit: str = G.EXPECTED_ATTEMPT1_PAPER_COMMIT,
                       stop_events: int = 1) -> Path:
    root = tmp_path / G.ATTEMPT1_ROOT_NAME
    for base, family in A1_BASES.items():
        saved = root / "EVIDENCE" / base / "final" / "saved"
        files = {}
        for rel, payload in (("adapter/README.md", b"readme"), ("adapter/adapter_config.json", b"{}"),
                             ("adapter/adapter_model.safetensors", b"adapter-" + base.encode()),
                             ("heads.safetensors", b"heads-" + base.encode())):
            (saved / rel).parent.mkdir(parents=True, exist_ok=True)
            (saved / rel).write_bytes(payload)
            files[rel] = hashlib.sha256(payload).hexdigest()
        _write(saved / "manifest.json", {**_saved_describe(family), "files": files})
        _write(root / "EVIDENCE" / base / "final" / "manifest.json", {
            **_attempt1_final_manifest(base, family), "model_files_sha256": files})
    journal = [{"event": "campaign_start", "utc": "2026-10-27T13:02:39Z",
                "pins": {"paper": {"commit": paper_commit, "branch": "trackp-20261026", "dirty": False}}}]
    journal += [{"event": "STOP", "utc": "2026-10-29T01:25:17Z", "gpu_seconds_total": gpu_seconds,
                 "error": "unit failed"} for _ in range(stop_events)]
    (root / "journal.jsonl").write_text("\n".join(json.dumps(event) for event in journal) + "\n")
    (tmp_path / "gpu_lease_log.jsonl").write_text(
        json.dumps({"event": "start", "pid": 11, "monotonic_s": 100.0}) + "\n" +
        json.dumps({"event": "end", "pid": 11, "monotonic_s": 130.0}) + "\n")
    return root


def _ns(tmp_path, **over):
    values = {"root": tmp_path / (G.NEW_ROOT_PREFIX + "20261116T1200Z"), "probes_only": True,
              "base": G.PROBES_ONLY_BASE, "attempt1_root": tmp_path / G.ATTEMPT1_ROOT_NAME,
              "a3_short": True, "authorization_amend_sha256": G.AUTHORIZATION_AMEND_SHA256}
    values.update(over)
    return SimpleNamespace(**values)


# ------------------------------------------------------------------ parser / flags

def test_parse_args_accepts_the_probes_only_contract(tmp_path):
    attempt1 = tmp_path / G.ATTEMPT1_ROOT_NAME
    args = G.parse_args(["--root", str(tmp_path / "p3a_attempt2_20261116T1200Z"), "--probes-only",
                         "--base", G.PROBES_ONLY_BASE, "--attempt1-root", str(attempt1), "--a3-short",
                         "--authorization-amend-sha256", G.AUTHORIZATION_AMEND_SHA256])
    assert args.probes_only and args.a3_short and args.base == G.PROBES_ONLY_BASE
    assert args.attempt1_root == attempt1 and args.authorization_amend_sha256 == G.AUTHORIZATION_AMEND_SHA256
    # the attempt-1 multi-base path defaults are unchanged when the new flags are absent
    old = G.parse_args(["--root", str(tmp_path / "campaign")])
    assert not old.probes_only and old.base is None and old.attempt1_root is None
    assert not old.a3_short and old.authorization_amend_sha256 is None


@pytest.mark.parametrize("over, match", [
    ({"attempt1_root": None}, "attempt1-root"),
    ({"base": None}, "needs --base"),
    ({"base": "kev-0.8b"}, "re-runs only"),
    ({"a3_short": False}, "needs --a3-short"),
    ({"authorization_amend_sha256": None}, "needs --authorization-amend-sha256"),
    ({"authorization_amend_sha256": "0" * 64}, "not the reviewed"),
])
def test_validate_probes_only_refuses_missing_or_wrong_flags(tmp_path, over, match):
    with pytest.raises(G.R.TrackPStop, match=match):
        G.validate_probes_only_args(_ns(tmp_path, **over))


def test_validate_probes_only_refuses_existing_nested_or_reused_roots(tmp_path):
    args = _ns(tmp_path)
    args.root.mkdir(parents=True)
    with pytest.raises(G.R.TrackPStop, match="already exists"):
        G.validate_probes_only_args(args)
    args = _ns(tmp_path, root=tmp_path / "not-an-attempt2-root")
    with pytest.raises(G.R.TrackPStop, match=G.NEW_ROOT_PREFIX):
        G.validate_probes_only_args(args)
    attempt1 = tmp_path / G.ATTEMPT1_ROOT_NAME
    args = _ns(tmp_path, root=attempt1)                       # attempt-1 root itself (and its name)
    with pytest.raises(G.R.TrackPStop, match="may not be reused|new p3a_attempt2"):
        G.validate_probes_only_args(args)
    args = _ns(tmp_path, root=attempt1 / "p3a_attempt2_20261116T1200Z")   # nested in attempt 1
    with pytest.raises(G.R.TrackPStop, match="may not be reused"):
        G.validate_probes_only_args(args)
    args = _ns(tmp_path, root=tmp_path / "p3a_attempt2_parent")           # would contain attempt-1 root
    args.attempt1_root = args.root / G.ATTEMPT1_ROOT_NAME
    with pytest.raises(G.R.TrackPStop, match="may not be reused"):
        G.validate_probes_only_args(args)
    args = _ns(tmp_path, root=Path("relative/p3a_attempt2_x"))
    with pytest.raises(G.R.TrackPStop, match="absolute"):
        G.validate_probes_only_args(args)


def test_old_path_refuses_probes_only_flags(tmp_path, monkeypatch):
    monkeypatch.setattr(G.socket, "gethostname", lambda: "TASL-7")
    monkeypatch.setattr(G.R, "authorization_note", lambda phase: tmp_path / "note.md")
    with pytest.raises(G.R.TrackPStop, match="probes-only"):
        G.main(["--root", str(tmp_path / "campaign"), "--base", G.PROBES_ONLY_BASE])


# ------------------------------------------------------------------ budget guard

def test_budget_math_seeds_from_attempt1_and_refuses_crossing_projection(tmp_path):
    budget = G.Attempt2Budget(G.ATTEMPT1_GPU_SECONDS_TOTAL, tmp_path / "gpu_lease_log.jsonl")
    record = budget.record()
    assert record["attempt1_gpu_seconds"] == pytest.approx(G.ATTEMPT1_GPU_SECONDS_TOTAL)
    assert record["attempt1_gpu_hours"] == pytest.approx(36.318161, abs=1e-5)
    assert record["remaining_hours"] == pytest.approx(8.681839, abs=1e-5)
    assert record["limit_seconds"] == 45 * 3600 and record["cap_seconds"] == 60 * 3600
    budget.require_available(600.0)                              # a short unit fits
    with pytest.raises(G.R.TrackPStop, match="45 GPU-hour"):
        budget.require_available(9 * 3600)                       # its projection does not
    remaining = 45 * 3600 - budget.used
    with pytest.raises(G.R.TrackPStop, match="45 GPU-hour"):
        budget.require_available(remaining + 1.0)                # the remaining time + 1 s is the STOP


def test_new_lease_log_time_is_added_and_incomplete_pairs_are_not(tmp_path):
    lease = tmp_path / "gpu_lease_log.jsonl"
    budget = G.Attempt2Budget(G.ATTEMPT1_GPU_SECONDS_TOTAL, lease)
    assert budget.used == pytest.approx(G.ATTEMPT1_GPU_SECONDS_TOTAL)
    lease.write_text(json.dumps({"event": "start", "pid": 7, "monotonic_s": 100.0}) + "\n")
    budget.refresh()
    assert budget.used == pytest.approx(G.ATTEMPT1_GPU_SECONDS_TOTAL)     # open interval not recorded
    with lease.open("a") as fh:
        fh.write(json.dumps({"event": "end", "pid": 7, "monotonic_s": 112.5}) + "\n")
    assert budget.refresh() == pytest.approx(G.ATTEMPT1_GPU_SECONDS_TOTAL + 12.5)
    with lease.open("a") as fh:                                           # a second completed unit
        fh.write(json.dumps({"event": "start", "pid": 8, "monotonic_s": 200.0}) + "\n")
        fh.write(json.dumps({"event": "end", "pid": 8, "monotonic_s": 260.0}) + "\n")
    assert budget.refresh() == pytest.approx(G.ATTEMPT1_GPU_SECONDS_TOTAL + 72.5)
    assert G.lease_log_total(tmp_path / "missing.jsonl") == 0.0


def test_60_hour_cap_is_recorded_and_enforced(tmp_path):
    budget = G.Attempt2Budget(G.ATTEMPT1_GPU_SECONDS_TOTAL, tmp_path / "lease.jsonl",
                              cap_seconds=int(G.ATTEMPT1_GPU_SECONDS_TOTAL) - 1)
    assert budget.record()["cap_hours"] == pytest.approx((int(G.ATTEMPT1_GPU_SECONDS_TOTAL) - 1) / 3600)
    with pytest.raises(G.R.TrackPStop, match="60 GPU-hour"):
        budget.require_available()


# ------------------------------------------------------------------ attempt-1 provenance

def test_attempt1_provenance_journal_and_lease_hashes(tmp_path):
    root = make_attempt1_root(tmp_path)
    provenance = G.build_attempt1_provenance(root)
    assert provenance["journal_sha256"] == hashlib.sha256((root / "journal.jsonl").read_bytes()).hexdigest()
    assert provenance["lease_log_sha256"] == hashlib.sha256((tmp_path / "gpu_lease_log.jsonl").read_bytes()).hexdigest()
    assert provenance["paper_commit"] == G.EXPECTED_ATTEMPT1_PAPER_COMMIT
    assert provenance["gpu_seconds_total"] == pytest.approx(G.ATTEMPT1_GPU_SECONDS_TOTAL)
    assert provenance["gpu_hours_total"] == pytest.approx(36.318161, abs=1e-5)
    assert provenance["recorded_at_run_time"] is False and provenance["label"] == "derived"
    assert provenance["derived_order"] == "history_first"
    assert provenance["derived_template_id"] == G.EXPECTED_DERIVED_TEMPLATE_IDS["qwen_control"]
    assert provenance["derivation"]["doc"] == G.M13_ORDER_RECORD


def test_attempt1_provenance_refuses_an_unpreserved_or_unreviewed_attempt1(tmp_path, monkeypatch):
    root = make_attempt1_root(tmp_path)
    with pytest.raises(G.R.TrackPStop, match="journal_sha256"):
        G.assert_attempt1_pins(G.build_attempt1_provenance(root))          # synthetic != reviewed sha
    provenance = G.build_attempt1_provenance(root)
    for key, value in (("EXPECTED_ATTEMPT1_JOURNAL_SHA256", provenance["journal_sha256"]),
                       ("EXPECTED_ATTEMPT1_LEASE_LOG_SHA256", provenance["lease_log_sha256"]),
                       ("EXPECTED_ATTEMPT1_PAPER_COMMIT", provenance["paper_commit"]),
                       ("ATTEMPT1_GPU_SECONDS_TOTAL", provenance["gpu_seconds_total"])):
        monkeypatch.setattr(G, key, value)
    G.assert_attempt1_pins(provenance)                                     # now consistent
    (tmp_path / "gpu_lease_log.jsonl").unlink()
    with pytest.raises(G.R.TrackPStop, match="lease log missing"):
        G.build_attempt1_provenance(root)
    (tmp_path / "gpu_lease_log.jsonl").write_text("{}\n")
    no_stop = tmp_path / G.ATTEMPT1_ROOT_NAME / "journal.jsonl"
    no_stop.write_text(json.dumps({"event": "campaign_start", "pins": {"paper": {"commit": "x"}}}) + "\n")
    with pytest.raises(G.R.TrackPStop, match="exactly one STOP"):
        G.build_attempt1_provenance(root)


def test_attempt1_input_hashes_every_loaded_file_and_refuses_tampering(tmp_path):
    root = make_attempt1_root(tmp_path)
    bound = G.attempt1_input(root, "qwen3.5-4b-base")
    saved = root / "EVIDENCE" / "qwen3.5-4b-base" / "final" / "saved"
    recorded = json.loads((root / "EVIDENCE" / "qwen3.5-4b-base" / "final" / "manifest.json").read_text())
    assert bound["loaded_artifact"] == str(saved)
    assert bound["model_files_sha256"] == recorded["model_files_sha256"]
    assert set(bound["loaded_hash"]["files_sha256"]) == set(recorded["model_files_sha256"]) | {"manifest.json"}
    assert len(bound["loaded_hash"]["composite_sha256"]) == 64
    assert bound["saved_describe"]["family"] == "qwen_control"
    # a changed byte in the preserved model is a STOP (never hash-check one file only)
    (saved / "heads.safetensors").write_bytes(b"tampered")
    with pytest.raises(G.R.TrackPStop, match="does not match"):
        G.attempt1_input(root, "qwen3.5-4b-base")


# ------------------------------------------------------------------ M13 template block

def test_template_block_matches_the_m13_record(tmp_path):
    kev_encoder = {"commit": KEV_COMMIT, "model_sha256": "a" * 64}
    kev = G.template_block("kev", _attempt1_final_manifest("kev-0.8b", "kev"), _saved_describe("kev"),
                           kev_encoder=kev_encoder)
    qwen = G.template_block("qwen_control", _attempt1_final_manifest("qwen3.5-4b-base", "qwen_control"),
                            _saved_describe("qwen_control"))
    assert set(kev) == {"version", "version_source", "family", "frame", "order", "field_order", "readout",
                        "encoder", "wrapper_config", "template_id"}
    assert kev["version"] == "trackp_prompt/v1" and kev["version_source"] == "r1/c3/train/types.py:26"
    assert kev["frame"] == "kev_pointer_v1" and kev["order"] == "history_first"
    assert kev["field_order"] == ["state", "proposal", "question", "options", "decide"]
    assert kev["readout"]["decide_token"] == "<|fim_suffix|>"
    assert kev["encoder"] == {"kind": "kev.model.encode", "repo": "jaredpalmer/kev", "commit": KEV_COMMIT,
                              "kev_model_sha256": "a" * 64, "id": f"kev@{KEV_COMMIT}"}
    assert kev["wrapper_config"] == {"kev_hybrid": True, "pointer_temperature": 1.0,
                                     "released_temperature": 2.35}
    assert kev["template_id"] == G.EXPECTED_DERIVED_TEMPLATE_IDS["kev"]
    assert qwen["frame"] == "qwen_bintoken_v1"
    assert qwen["field_order"] == ["state", "proposal", "question", "bins", "belief", "action"]
    assert qwen["wrapper_config"] == {"list_bins": True, "bin_order": list(range(12))}
    assert qwen["template_id"] == G.EXPECTED_DERIVED_TEMPLATE_IDS["qwen_control"]
    assert G.prompt_version() == G.EXPECTED_PROMPT_VERSION


def test_template_block_refuses_a_changed_encoder_or_wrapper(tmp_path):
    kev_encoder = {"commit": KEV_COMMIT, "model_sha256": "a" * 64}
    manifest = _attempt1_final_manifest("kev-0.8b", "kev")
    manifest["environment"]["packages"]["kev"]["pip_commit"] = "f" * 40
    with pytest.raises(G.R.TrackPStop, match="Kev encoder mismatch"):
        G.template_block("kev", manifest, _saved_describe("kev"), kev_encoder=kev_encoder)
    qwen_manifest = _attempt1_final_manifest("qwen3.5-4b-base", "qwen_control")
    qwen_manifest["environment"]["transformers"] = "5.18.0"               # a different template than attempt 1
    assert G.template_block("qwen_control", qwen_manifest, _saved_describe("qwen_control"))["template_id"] \
        not in G.EXPECTED_DERIVED_TEMPLATE_IDS.values()
    bad_wrapper = dict(_saved_describe("qwen_control"), bin_order=list(reversed(range(12))))
    with pytest.raises(G.R.TrackPStop, match="canonical bins"):
        G.wrapper_config_block("qwen_control", bad_wrapper)


def test_sidecar_builder_writes_every_m13_field(tmp_path):
    root = make_attempt1_root(tmp_path)
    provenance = G.build_attempt1_provenance(root)
    inputs = {base: G.attempt1_input(root, base) for base in A1_BASES}
    kev_encoder = {"commit": KEV_COMMIT, "model_sha256": "a" * 64}
    templates = {family: G.template_block(family, _attempt1_final_manifest(base, family),
                                          inputs[base]["saved_describe"], kev_encoder=kev_encoder)
                 for base, family in A1_BASES.items()}
    build = G.make_sidecar_builder(provenance, inputs, templates, kev_encoder, G.AUTHORIZATION_AMEND_SHA256)
    unit_dir = tmp_path / "EVIDENCE" / "qwen3.5-4b-base" / "probes"
    _write(unit_dir / "manifest.json", _attempt1_final_manifest("qwen3.5-4b-base", "qwen_control"))
    _write(unit_dir / "report.json", {"A3": {"protocol": "v2_budget"}})
    sidecar = build(report={"A3": {"protocol": "v2_budget"}},
                    manifest=_attempt1_final_manifest("qwen3.5-4b-base", "qwen_control"),
                    directory=unit_dir, label="EVIDENCE", base="qwen3.5-4b-base", name="probes",
                    budget=None, gpu_seconds_unit=12.5)
    assert sidecar["schema"] == G.UNIT_MANIFEST_SCHEMA
    assert sidecar["unit"] == {"label": "EVIDENCE", "base": "qwen3.5-4b-base", "unit": "probes",
                               "run_dir": str(unit_dir)}
    assert sidecar["attempt2_template"] == templates["qwen_control"]
    assert sidecar["attempt1_provenance"]["journal_sha256"] == provenance["journal_sha256"]
    assert sidecar["attempt1_input"]["model_files_sha256"] == inputs["qwen3.5-4b-base"]["model_files_sha256"]
    assert sidecar["inputs"]["child_report_sha256"] == hashlib.sha256((unit_dir / "report.json").read_bytes()).hexdigest()
    assert sidecar["inputs"]["authorization_amend_sha256"] == G.AUTHORIZATION_AMEND_SHA256
    assert sidecar["cost"] == {"gpu_seconds": 12.5}


# ------------------------------------------------------------------ command sequence

def test_probes_only_units_are_exactly_the_two_intended_commands(tmp_path):
    attempt1 = tmp_path / G.ATTEMPT1_ROOT_NAME
    units = G.probes_only_units(attempt1)
    assert [(unit["label"], unit["base"], unit["unit"]) for unit in units] == [
        ("DRYRUN", "kev-0.8b", "probes"), ("EVIDENCE", "qwen3.5-4b-base", "probes")]
    assert units[0]["arguments"] == [
        "probes", "--base", "kev-0.8b", "--head-form", "linear12", "--budget", "--a3-short",
        "--n-probe", "8", "--load", str(attempt1 / "EVIDENCE/kev-0.8b/final/saved")]
    assert units[1]["arguments"] == [
        "probes", "--base", "qwen3.5-4b-base", "--head-form", "linear12", "--budget", "--a3-short",
        "--n-probe", "100", "--load", str(attempt1 / "EVIDENCE/qwen3.5-4b-base/final/saved")]
    assert [unit["projection_seconds"] for unit in units] == [G.PROJECTED_SECONDS["DRYRUN"],
                                                              G.PROJECTED_SECONDS["EVIDENCE"]]


def test_verify_a3_short_report_requires_the_changed_path(tmp_path):
    good = {"A3": {"protocol": "v2_budget"},
            "A3_descriptive": {"skipped": G.A3_SHORT_MARKER, "levels": list(G.A3_DESCRIPTIVE_LEVELS),
                               "pass": None}}
    G.verify_a3_short_report(good, "DRYRUN", "tid")
    for broken in ({"A3": {}, "A3_descriptive": good["A3_descriptive"]},
                   {"A3": {"protocol": "v2_budget"}, "A3_descriptive": {"pass": None}},
                   {"A3": {"protocol": "v2_budget"},
                    "A3_descriptive": {"skipped": G.A3_SHORT_MARKER, "levels": [2000, 8000], "pass": True}},
                   {"A3": {"protocol": "v2_budget"},
                    "A3_descriptive": {"skipped": G.A3_SHORT_MARKER, "levels": [2000], "pass": None}}):
        with pytest.raises(G.R.TrackPStop):
            G.verify_a3_short_report(broken, "DRYRUN", "tid")


def test_marker_begin_and_end_are_recorded_even_on_stop(tmp_path):
    calls = []

    def fake_run_marker(helper, action):
        calls.append((helper, action))
        return {"command": [helper, action, G.MARKER_PHASE], "utc": "now", "rc": 0, "stdout": "", "stderr": ""}

    mp = pytest.MonkeyPatch()
    mp.setattr(G, "run_marker", fake_run_marker)
    try:
        journal = tmp_path / "journal.jsonl"
        state = {}
        with pytest.raises(RuntimeError, match="boom"):
            with G.evidence_marker(journal, {"path": "helper"}, state):
                raise RuntimeError("boom")
        events = [json.loads(line)["event"] for line in journal.read_text().splitlines()]
        assert events == ["marker_begin", "marker_end"]
        assert calls == [("helper", "begin"), ("helper", "end")]
        assert state["marker_end"]["rc"] == 0
        mp.setattr(G, "run_marker", lambda helper, action: {"command": [], "utc": "now", "rc": 1, "stdout": "",
                                                            "stderr": "marker belongs to another phase"})
        with pytest.raises(G.R.TrackPStop, match="begin"):
            with G.evidence_marker(tmp_path / "j2", {"path": "helper"}):
                pass
    finally:
        mp.undo()


# ------------------------------------------------------------------ end-to-end (stubbed child)

def _campaign_fixture(tmp_path, monkeypatch):
    attempt1 = make_attempt1_root(tmp_path)
    monkeypatch.setattr(G, "attempt1_environment", lambda: {"PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"})
    monkeypatch.setattr(G, "verify_probes_only_pins", lambda amend, disk_path=None: {
        "boot_id": "boot-2c9bb104", "hostname": "TASL-7", "paper": {"commit": "a" * 40},
        "harness": {"commit": G.HARNESS_PIN},
        "marker": {"path": "helper", "sha256": G.EXPECTED_MARKER_SHA256, "phase": G.MARKER_PHASE},
        "authorization_amend_file_present": False})
    monkeypatch.setattr(G, "assert_attempt1_pins", lambda provenance: None)
    monkeypatch.setattr(G, "installed_kev_encoder",
                        lambda: {"commit": KEV_COMMIT, "model_sha256": "a" * 64})
    monkeypatch.setattr(G, "run_marker", lambda helper, action: {
        "command": [helper, action, G.MARKER_PHASE], "utc": "now", "rc": 0, "stdout": "", "stderr": ""})
    return attempt1


def test_campaign_runs_exactly_dryrun_then_evidence(tmp_path, monkeypatch):
    attempt1 = _campaign_fixture(tmp_path, monkeypatch)
    calls, sidecars = [], []

    def fake_run_unit(root, journal, boot_id, budget, label, base, name, arguments, gpu=True, **kw):
        calls.append({"label": label, "base": base, "name": name, "arguments": list(arguments),
                      "template_id": kw.get("template_id"), "projection_seconds": kw.get("projection_seconds"),
                      "attempt1_input": kw.get("attempt1_input")})
        directory = Path(root) / label / base / name
        manifest = json.loads((attempt1 / "EVIDENCE" / base / "final" / "manifest.json").read_text())
        report = {"A3": {"protocol": "v2_budget"},
                  "A3_descriptive": {"skipped": G.A3_SHORT_MARKER, "levels": list(G.A3_DESCRIPTIVE_LEVELS),
                                     "pass": None}}
        G._write_json(directory / "report.json", report)
        G._write_json(directory / "manifest.json", manifest)
        mirror = Path(kw["lease_mirror"])
        with mirror.open("a") as fh:
            fh.write(json.dumps({"event": "start", "pid": 100 + len(calls), "monotonic_s": 1000.0}) + "\n")
            fh.write(json.dumps({"event": "end", "pid": 100 + len(calls), "monotonic_s": 1010.0}) + "\n")
        sidecars.append(kw["sidecar_builder"](report=report, manifest=manifest, directory=directory,
                                              label=label, base=base, name=name, budget=budget,
                                              gpu_seconds_unit=1.0))
        return report

    monkeypatch.setattr(G, "run_unit", fake_run_unit)
    args = _ns(tmp_path)
    G.run_probes_only_campaign(args)
    assert [(call["label"], call["base"]) for call in calls] == [("DRYRUN", "kev-0.8b"),
                                                                 ("EVIDENCE", "qwen3.5-4b-base")]
    assert calls[0]["arguments"] == G.probes_only_units(attempt1)[0]["arguments"]
    assert calls[1]["arguments"] == G.probes_only_units(attempt1)[1]["arguments"]
    assert calls[0]["template_id"] == G.EXPECTED_DERIVED_TEMPLATE_IDS["kev"]
    assert calls[1]["template_id"] == G.EXPECTED_DERIVED_TEMPLATE_IDS["qwen_control"]
    assert calls[1]["attempt1_input"]["loaded_artifact"].endswith("qwen3.5-4b-base/final/saved")
    assert [sidecar["schema"] for sidecar in sidecars] == [G.UNIT_MANIFEST_SCHEMA] * 2
    events = [json.loads(line) for line in (args.root / "journal.jsonl").read_text().splitlines()]
    names = [event["event"] for event in events]
    assert names[0] == "campaign_start" and names[-1] == "complete"
    assert names.index("marker_begin") < names.index("marker_end")
    start = events[0]
    assert start["mode"] == "probes_only"
    assert start["serialisation_schema"] == G.UNIT_MANIFEST_SCHEMA
    assert set(start["templates"]) == {"kev", "qwen_control"}
    assert start["attempt1_provenance"]["gpu_seconds_total"] == pytest.approx(G.ATTEMPT1_GPU_SECONDS_TOTAL)
    assert start["attempt1_provenance"]["recorded_at_run_time"] is False
    assert set(start["attempt1_provenance"]["loaded_artifacts"]) == set(A1_BASES)
    assert start["budget"]["attempt1_gpu_hours"] == pytest.approx(36.318161, abs=1e-5)
    assert start["gpu_limit_seconds"] == 45 * 3600 and start["gpu_cap_seconds"] == 60 * 3600
    unit_events = [event for event in events if event["event"] in ("unit_start", "unit_complete")]
    assert all("template_id" in event for event in unit_events)
    assert (args.root / "gpu_lease_log.jsonl").exists()             # the new root gets its own lease log
    assert events[-1]["budget"]["new_lease_seconds"] == pytest.approx(20.0)   # recorded, and added to attempt 1
    assert events[-1]["budget"]["cap_seconds"] == 60 * 3600


def test_campaign_stops_before_evidence_if_the_dryrun_is_not_the_changed_path(tmp_path, monkeypatch):
    attempt1 = _campaign_fixture(tmp_path, monkeypatch)
    calls = []

    def fake_run_unit(root, journal, boot_id, budget, label, base, name, arguments, gpu=True, **kw):
        calls.append(label)
        directory = Path(root) / label / base / name
        G._write_json(directory / "report.json", {"A3": {"protocol": "v2_budget"},
                                                  "A3_descriptive": {"ran": [0], "pass": None}})
        G._write_json(directory / "manifest.json",
                      json.loads((attempt1 / "EVIDENCE" / base / "final" / "manifest.json").read_text()))
        return {"A3": {"protocol": "v2_budget"}, "A3_descriptive": {"ran": [0], "pass": None}}

    monkeypatch.setattr(G, "run_unit", fake_run_unit)
    args = _ns(tmp_path)
    with pytest.raises(G.R.TrackPStop, match="A3-descriptive|A3_descriptive"):
        G.run_probes_only_campaign(args)
    assert calls == ["DRYRUN"]                                   # no EVIDENCE unit, no retry
    events = [json.loads(line) for line in (args.root / "journal.jsonl").read_text().splitlines()]
    assert events[-1]["event"] == "STOP"
    assert events[-1]["template_id"] == G.EXPECTED_DERIVED_TEMPLATE_IDS["kev"]
    assert events[-1]["marker_end"]["rc"] == 0                   # marker ended on STOP
    assert not (args.root / "EVIDENCE").exists()


# ------------------------------------------------------------------ run_unit attempt-2 wiring

class _DummyWatchdog:
    def poll(self):
        return None

    def wait(self, timeout=None):  # noqa: ARG002
        return 0


def test_run_unit_writes_runner_manifest_records_template_and_mirrors_the_lease(tmp_path, monkeypatch):
    fake = tmp_path / "fake.py"
    fake.write_text('''
import json, os, pathlib, sys, time
args = sys.argv
lease = pathlib.Path(args[args.index("--lease") + 1])
out = pathlib.Path(args[args.index("--run-dir") + 1]); out.mkdir()
label = args[args.index("--evidence") + 1]
driver = {"boot_id": "boot"}
start = {"event": "start", "job": "probes", "pid": os.getpid(), "utc": "now",
         "monotonic_s": time.monotonic(), "tasl7_driver": driver}
lease.open("a").write(json.dumps(start) + "\\n")
time.sleep(0.05)
end = {"event": "end", "job": "probes", "pid": os.getpid(), "utc": "now",
       "monotonic_s": time.monotonic(), "tasl7_driver": driver}
lease.open("a").write(json.dumps(end) + "\\n")
(out / "report.json").write_text(json.dumps({"A3": {"protocol": "v2_budget"}}))
(out / "manifest.json").write_text(json.dumps({"evidence_label": label, "tasl7_driver": {"boot_id": "boot"},
                                              "gpu_lease": [start, end]}))
''')
    monkeypatch.setattr(G, "SCRIPT", fake)
    monkeypatch.setattr(G, "verify_live_pins", lambda journal: None)
    monkeypatch.setattr(G.R, "tasl7_driver_snapshot", lambda: {"boot_id": "boot"})
    monkeypatch.setattr(G, "worker_parent_death_guard", lambda parent: None)
    monkeypatch.setattr(G, "start_watchdog", lambda *args, **kwargs: _DummyWatchdog())
    monkeypatch.setattr(G.time, "sleep", lambda seconds: None)
    root = tmp_path / "campaign"
    root.mkdir()
    journal, lease, mirror = root / "journal.jsonl", tmp_path / "lease.jsonl", root / "gpu_lease_log.jsonl"
    sidecar = {"schema": G.UNIT_MANIFEST_SCHEMA, "unit": {"label": "DRYRUN"}}
    seen = {}
    result = G.run_unit(root, journal, "boot", G.GPUBudget(lease_log=lease), "DRYRUN", "kev", "probes",
                        ["probes", "--lease", str(lease)], gpu=True, template_id="tid-kev",
                        attempt1_input={"root": "/attempt1"}, projection_seconds=5.0, lease_mirror=mirror,
                        sidecar_builder=lambda **kw: seen.update(kw) or sidecar)
    assert result == {"A3": {"protocol": "v2_budget"}}
    path = root / "DRYRUN" / "kev" / "probes" / "runner_manifest.json"
    assert json.loads(path.read_text()) == sidecar
    events = [json.loads(line) for line in journal.read_text().splitlines()]
    assert [event["event"] for event in events] == ["unit_start", "unit_complete"]
    assert events[0]["template_id"] == "tid-kev" and events[0]["attempt1_input"] == {"root": "/attempt1"}
    assert events[1]["template_id"] == "tid-kev"
    assert events[1]["gpu_seconds_unit"] == pytest.approx(0.05, abs=0.02)
    assert events[1]["runner_manifest_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    mirrored = [json.loads(line) for line in mirror.read_text().splitlines()]
    assert [event["event"] for event in mirrored] == ["start", "end"]
    assert G.lease_log_total(mirror) == pytest.approx(0.05, abs=0.02)
    assert seen["base"] == "kev" and seen["gpu_seconds_unit"] == pytest.approx(0.05, abs=0.02)


def test_run_unit_refuses_a_crossing_projection_before_any_child(tmp_path, monkeypatch):
    monkeypatch.setattr(G.R, "tasl7_driver_snapshot", lambda: {"boot_id": "boot"})
    root = tmp_path / "campaign"
    root.mkdir()
    budget = G.Attempt2Budget(G.ATTEMPT1_GPU_SECONDS_TOTAL, tmp_path / "new_lease.jsonl")
    with pytest.raises(G.R.TrackPStop, match="45 GPU-hour"):
        G.run_unit(root, root / "journal.jsonl", "boot", budget, "EVIDENCE", "qwen3.5-4b-base", "probes", [],
                   projection_seconds=9 * 3600)
    assert not (root / "journal.jsonl").exists()
    assert not (root / "EVIDENCE").exists()
