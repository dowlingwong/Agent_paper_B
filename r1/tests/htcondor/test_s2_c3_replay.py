"""Synthetic tests for the S2-C3 L40S deployment-check replay unit (no GPU, no network, no HTCondor, no /ceph).

Covers: replay-spec validation negatives (every pin), the pinned-input SHA256SUMS verification, the byte-scoped
job.json rewrite (only out/base_url), the B2 configuration-binding recomputation/refusal, the audit-seed guards
(9201-9210 only; 7001-7010 refused; no B.2 audit), the reviewed label patch (scope check, sha record, clean
authorization checkout), the authorization gate pre-flight/STOP, campaign-manifest validation, the criteria 1-6
comparison maths at every tolerance boundary, the hard STOPs of the comparison, the JDL renderer, and the reuse of
the S2-C2 seal guards.
"""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "sweep2"))
import s2_c2_lib as lib  # noqa: E402
import s2_c3_compare as compare  # noqa: E402
import s2_c3_replay as replay  # noqa: E402
import render_jdl  # noqa: E402

SPEC = json.loads((ROOT / "sweep2" / "spec.replay.example.json").read_text())
PATCH = ROOT / "sweep2" / "s2_c3_label_patch.diff"
INPUTS = ROOT / replay.INPUTS_DIR


def spec_copy():
    return copy.deepcopy(SPEC)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ------------------------------------------------------------------ spec validation
def test_example_spec_validates_and_is_engineering_only():
    validated = replay.validate_spec(spec_copy())
    assert validated["node"] == "digits_mlp" and validated["run_id"] == "s2c3-20261117-b"
    assert validated["spec"]["label"]["execution_label"] == "ENGINEERING_ONLY"


@pytest.mark.parametrize("mutate", [
    lambda s: s.__setitem__("schema", "s2_c3_replay/v2"),
    lambda s: s.__setitem__("schema", "s2_c2_job/v1"),
    lambda s: s.__setitem__("kind", "chunk"),
    lambda s: s.__setitem__("dryrun", False),
    lambda s: s.__setitem__("evidence", True),
    lambda s: s.__setitem__("b2_audits", "yes"),
    lambda s: s.__setitem__("chunk_id", "openml_ionosphere"),
    lambda s: s.__setitem__("node", "tabular_mlp"),
    lambda s: s["image"].__setitem__("digest", "ghcr.io/other@sha256:" + "0" * 64),
    lambda s: s["image"].__setitem__("llama_server_sha256", "0" * 64),
    lambda s: s["image"]["versions_markers"].__setitem__("image", "r1-htc-cpu"),
    lambda s: s["paper"].__setitem__("commit", "9" * 40),
    lambda s: s["paper"].__setitem__("b2_authorization_note", "docs/r1/authorizations/other.md"),
    lambda s: s["harness"].__setitem__("commit", "897d83c8efa364ec2fdd37288241cc42e01d7274"),
    lambda s: s["model"].__setitem__("sha256", "0" * 64),
    lambda s: s["model"].__setitem__("size", 1),
    lambda s: s["model"].__setitem__("alias", "other_model"),
    lambda s: s["server"].__setitem__("ctx", 16384),
    lambda s: s["server"].__setitem__("n_gpu_layers", 99),
    lambda s: s["server"].__setitem__("expected_build", "other"),
    lambda s: s["server"].__setitem__("extra_args", ["--jinja"]),
    lambda s: s["replay_inputs"].__setitem__("sha256sums_sha256", "0" * 64),
    lambda s: s["replay_inputs"].__setitem__("dir", "docs/other"),
    lambda s: s["replay_inputs"].__setitem__("nodes", ["digits_mlp"]),
    lambda s: s["replay_inputs"]["roots"].pop(),
    lambda s: s["replay_inputs"].__setitem__("seeds", [9011, 9012, 9013, 9015]),
    lambda s: s["replay_inputs"].__setitem__("audit_seeds", [9201, 9202, 9203, 9204, 9205, 9206, 9207, 9208,
                                                             9209, 9211]),
    lambda s: s["replay_inputs"].__setitem__("audit_seeds", list(range(7001, 7011))),
    lambda s: s["replay_inputs"].__setitem__("binding", "0" * 64),
    lambda s: s["label"].__setitem__("execution_label", "EVIDENCE"),
    lambda s: s["label"].__setitem__("execution_label", "DRYRUN"),
    lambda s: s["label"].__setitem__("replay_marker", "other"),
    lambda s: s["label"].__setitem__("extra", "x"),
    lambda s: s["label_patch"].__setitem__("path", "sweep2/other.diff"),
    lambda s: s["label_patch"].__setitem__("sha256", "0" * 64),
    lambda s: s["criteria"].__setitem__("sha256", "0" * 64),
    lambda s: s["criteria"].__setitem__("path", "docs/other.md"),
    lambda s: s["requirements"].__setitem__("cloud_site", "BwForCluster-HoreKa"),
    lambda s: s["requirements"].__setitem__("gpu_device_name", "NVIDIA H200"),
    lambda s: s["requirements"].__setitem__("arch", "AARCH64"),
    lambda s: s["requirements"].__setitem__("opsys", "WINDOWS"),
    lambda s: s["requirements"].__setitem__("min_cpus", 8),
    lambda s: s["requirements"].__setitem__("cpu_family", 25),
    lambda s: s["requirements"].__setitem__("cpu_model_number", 1),
    lambda s: s["requirements"].__setitem__("cpu_model_contains", "AMD EPYC"),
    lambda s: s["requirements"].__setitem__("requires_etp_ceph", True),
    lambda s: s.__setitem__("walltime_s", 60),
    lambda s: s.__setitem__("walltime_s", 12204),
    lambda s: s.__setitem__("request_disk_kb", 128000),
    lambda s: s.__setitem__("request_memory_mb", 10853),
    lambda s: s.__setitem__("request_disk_kb", "42460970"),
    lambda s: s.__setitem__("request_memory_mb", None),
])
def test_spec_refuses_anything_else(mutate):
    spec = spec_copy()
    mutate(spec)
    with pytest.raises(replay.Stop):
        replay.validate_spec(spec)


def test_spec_missing_fields_are_stops():
    for key in ("image", "paper", "harness", "model", "server", "replay_inputs", "label", "label_patch",
                "criteria", "requirements", "run_id", "node", "walltime_s", "request_disk_kb",
                "request_memory_mb"):
        spec = spec_copy()
        del spec[key]
        with pytest.raises(replay.Stop):
            replay.validate_spec(spec)


def test_reserved_b2_audit_seeds_are_refused_explicitly():
    spec = spec_copy()
    spec["replay_inputs"]["seeds"] = [7001, 9012, 9013, 9014]
    with pytest.raises(replay.Stop, match="7001-7010"):
        replay.validate_spec(spec)


# ------------------------------------------------------------------ pinned inputs
def stage_inputs(dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(INPUTS / "SHA256SUMS", dest / replay.STAGED_SHA256SUMS)
    for root in replay.ROOTS:
        shutil.copy2(INPUTS / root / "job.json", dest / replay.STAGED_JOB.format(root=root))
        shutil.copy2(INPUTS / root / "campaign_manifest.json",
                     dest / replay.STAGED_MANIFEST.format(root=root))
    return dest


def rewrite_sums(stage: Path) -> None:
    lines = []
    for root in replay.ROOTS:
        for kind, staged in (("job.json", replay.STAGED_JOB.format(root=root)),
                             ("campaign_manifest.json", replay.STAGED_MANIFEST.format(root=root))):
            lines.append(f"{sha((stage / staged).read_bytes())}  {root}/{kind}")
    (stage / replay.STAGED_SHA256SUMS).write_text("\n".join(lines) + "\n")


def test_pinned_inputs_verify_and_tamper_is_a_stop(tmp_path):
    stage = stage_inputs(tmp_path / "stage")
    out = replay.verify_pinned_inputs(stage, SPEC)
    assert out["files"] == 24 and out["sha256sums_sha256"] == replay.INPUTS_SHA256SUMS_SHA256
    assert set(out["jobs"]) == set(replay.ROOTS)
    assert all(job["audit_seeds"] == list(replay.AUDIT_SEEDS) for job in out["jobs"].values())

    tampered = stage / replay.STAGED_JOB.format(root="digits_mlp__s9011")
    tampered.write_text(tampered.read_text().replace('"workers": 20', '"workers": 21'))
    with pytest.raises(replay.Stop, match="SHA256SUMS"):
        replay.verify_pinned_inputs(stage, SPEC)


def test_pinned_inputs_refuse_extra_or_missing_roots(tmp_path):
    stage = stage_inputs(tmp_path / "stage")
    (stage / replay.STAGED_JOB.format(root="digits_mlp__s9011")).unlink()
    with pytest.raises(replay.Stop, match="missing"):
        replay.verify_pinned_inputs(stage, SPEC)


def test_pinned_inputs_refuse_a_different_sha256sums_pin(tmp_path):
    stage = stage_inputs(tmp_path / "stage")
    sums = stage / replay.STAGED_SHA256SUMS
    sums.write_text(sums.read_text() + "\n")
    with pytest.raises(replay.Stop, match="sha256"):
        replay.verify_pinned_inputs(stage, SPEC)


def test_recorded_job_fields_are_checked():
    job = json.loads((INPUTS / "digits_mlp__s9011" / "job.json").read_text())
    replay._check_recorded_job("digits_mlp__s9011", job, SPEC)
    for mutate, match in (
        (lambda j: j.__setitem__("phase", "b1"), "phase"),
        (lambda j: j.__setitem__("mode", "on"), "mode"),
        (lambda j: j.__setitem__("dryrun", True), "dryrun"),
        (lambda j: j.__setitem__("W", 10), "W"),
        (lambda j: j.__setitem__("workers", 4), "workers"),
        (lambda j: j.__setitem__("llm_call_cap", 40), "llm_call_cap"),
        (lambda j: j.__setitem__("harness_commit", "8" * 40), "harness_commit"),
        (lambda j: j.__setitem__("authorization_checkout_head", "8" * 40), "authorization_checkout_head"),
        (lambda j: j.__setitem__("audit_seeds", list(range(7001, 7011))), "audit_seeds"),
        (lambda j: j.__setitem__("binding", "0" * 64), "binding"),
        (lambda j: j.__setitem__("node", "tabular_mlp"), "node"),
        (lambda j: j.__setitem__("seed", 9015), "seed"),
        (lambda j: j["candidate"].__setitem__("id", "other"), "candidate"),
        (lambda j: j["candidate"]["quant_source"].__setitem__("sha256", "0" * 64), "GGUF"),
        (lambda j: j["candidate"]["thinking_policy"].__setitem__("mode", "on"), "thinking"),
    ):
        bad = copy.deepcopy(job)
        mutate(bad)
        with pytest.raises(replay.Stop, match=match):
            replay._check_recorded_job("digits_mlp__s9011", bad, SPEC)


# ------------------------------------------------------------------ job.json rewrite
def test_rewrite_changes_only_out_and_base_url():
    original = (INPUTS / "digits_mlp__s9011" / "job.json").read_text()
    new_out = "/sandbox/out/digits_mlp__s9011"
    new_url = "http://127.0.0.1:18130/v1"
    rewritten = replay.rewrite_job_json(original, new_out, new_url)
    before, after = json.loads(original), json.loads(rewritten)
    changed = {key for key in before if before[key] != after[key]}
    assert changed == {"out", "base_url"}
    assert after["out"] == new_out and after["base_url"] == new_url
    changed_lines = [(a, b) for a, b in zip(original.splitlines(), rewritten.splitlines()) if a != b]
    assert len(changed_lines) == 2
    assert changed_lines[0][1].lstrip().startswith('"out"')
    assert changed_lines[1][1].lstrip().startswith('"base_url"')
    # The pinned canonical form round-trips, so a byte comparison proves nothing else moved.
    assert json.dumps(before, indent=2) + "\n" == original


def test_rewrite_refuses_a_noncanonical_job_json():
    original = (INPUTS / "digits_mlp__s9011" / "job.json").read_text()
    with pytest.raises(replay.Stop, match="canonical"):
        replay.rewrite_job_json(json.dumps(json.loads(original), indent=4), "/x", "http://y")


def test_rewrite_refuses_a_job_without_out_or_base_url():
    job = json.loads((INPUTS / "digits_mlp__s9011" / "job.json").read_text())
    del job["base_url"]
    with pytest.raises(replay.Stop, match="base_url"):
        replay.rewrite_job_json(json.dumps(job, indent=2) + "\n", "/x", "http://y")


def test_prepare_root_jobs_writes_only_the_sandbox_copies(tmp_path):
    stage = stage_inputs(tmp_path / "stage")
    pins = {root: sha((stage / replay.STAGED_JOB.format(root=root)).read_bytes()) for root in replay.ROOTS}
    pinned_before = {root: sha((stage / replay.STAGED_JOB.format(root=root)).read_bytes())
                     for root in replay.ROOTS}
    prepared = replay.prepare_root_jobs(stage, SPEC, "digits_mlp", pins,
                                        "http://127.0.0.1:18130/v1", replay.INPUTS_SHA256SUMS_SHA256)
    assert [entry["root"] for entry in prepared] == replay.ordered_roots("digits_mlp")
    for entry in prepared:
        job = json.loads(Path(entry["job_json"]).read_text())
        assert job["out"] == entry["out"] and job["base_url"] == "http://127.0.0.1:18130/v1"
        assert entry["changed_fields"] == ["out", "base_url"]
        assert entry["original_sha256"] != entry["rewritten_sha256"]
        assert Path(entry["job_json"]).parent == Path(entry["out"])
    # the staged pinned inputs are untouched by the preparation
    assert {root: sha((stage / replay.STAGED_JOB.format(root=root)).read_bytes())
            for root in replay.ROOTS} == pinned_before


def test_prepare_root_jobs_refuses_a_changed_pinned_job(tmp_path):
    stage = stage_inputs(tmp_path / "stage")
    pins = {root: sha((stage / replay.STAGED_JOB.format(root=root)).read_bytes()) for root in replay.ROOTS}
    pins["digits_mlp__s9011"] = "0" * 64
    with pytest.raises(replay.Stop, match="changed"):
        replay.prepare_root_jobs(stage, SPEC, "digits_mlp", pins, "http://x/v1",
                                 replay.INPUTS_SHA256SUMS_SHA256)


# ------------------------------------------------------------------ binding (the B2 ExamRunner method)
def test_recompute_binding_matches_the_recorded_b2_binding():
    job = json.loads((INPUTS / "digits_mlp__s9011" / "job.json").read_text())
    cfg = job["authority_config"]
    registry_sha = "2c6ef6b329694536df6a23345e4313d0cb2dcbf447113023e18f60fcb608e723"
    grids_sha = "7ab60c161433bf54d7392f7b3278b656a0e49ba1c28df05db81b410824b1ea14"
    binding = replay.recompute_binding(cfg, registry_sha, grids_sha)
    assert binding == replay.BINDING
    assert binding == job["binding"]
    # out/base_url are not inputs to the binding: changing them does not change it.
    rewritten = replay.rewrite_job_json((INPUTS / "digits_mlp__s9011" / "job.json").read_text(),
                                        "/sandbox/out/x", "http://127.0.0.1:18130/v1")
    assert replay.recompute_binding(json.loads(rewritten)["authority_config"], registry_sha, grids_sha) == binding
    assert replay.recompute_binding(cfg, "0" * 64, grids_sha) != binding


def test_verify_binding_refuses_a_committed_config_mismatch(tmp_path, monkeypatch):
    job = json.loads((INPUTS / "digits_mlp__s9011" / "job.json").read_text())
    jobs = {root: job for root in replay.ROOTS}

    def fake_blob(_paper_dir, rel):
        return json.dumps({"not": "the config"}).encode() if rel == replay.B2_CONFIG_REL else b"x"

    monkeypatch.setattr(replay, "git_blob", fake_blob)
    with pytest.raises(replay.Stop, match="committed B2 configuration"):
        replay.verify_binding(tmp_path, jobs, SPEC)


def test_verify_binding_positive_and_refuses_a_different_binding(tmp_path, monkeypatch):
    try:
        subprocess.check_output(["git", "-C", str(ROOT), "cat-file", "-e",
                                 f"{replay.PAPER_COMMIT}^{{commit}}"], stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("the pinned B2 commit is not available in this clone")

    job = json.loads((INPUTS / "digits_mlp__s9011" / "job.json").read_text())
    jobs = {root: job for root in replay.ROOTS}
    cfg = job["authority_config"]

    def pinned_blob(_paper_dir, rel):
        return subprocess.check_output(["git", "-C", str(ROOT), "show", f"{replay.PAPER_COMMIT}:{rel}"])

    monkeypatch.setattr(replay, "git_blob", pinned_blob)
    verified = replay.verify_binding(tmp_path, jobs, SPEC)
    assert verified["recomputed"] == replay.BINDING and verified["config_equals_committed"] is True
    bad = {root: dict(job, binding="0" * 64) for root in replay.ROOTS}
    with pytest.raises(replay.Stop, match="binding"):
        replay.verify_binding(tmp_path, bad, SPEC)


# ------------------------------------------------------------------ label patch
def test_label_patch_scope_is_the_execution_label_only():
    out = replay.check_patch_scope(PATCH.read_text())
    assert out["files"] == [replay.PATCH_TARGET]
    assert out["execution_label_only"] is True


def test_label_patch_scope_refuses_trial_audit_changes_or_other_files():
    text = PATCH.read_text()
    bad = text.replace("+    if job.get('dryrun'):",
                       "+    run_config(node, files, job['audit_seeds'], str(out))\n+    if job.get('dryrun'):")
    with pytest.raises(replay.Stop, match="outside the execution label|trial/audit"):
        replay.check_patch_scope(bad)
    other = text.replace("a/r1/exam/campaign.py", "a/r1/exam/runtime.py") \
                .replace("b/r1/exam/campaign.py", "b/r1/exam/runtime.py")
    with pytest.raises(replay.Stop, match="only"):
        replay.check_patch_scope(other)
    with pytest.raises(replay.Stop, match="empty"):
        replay.check_patch_scope("")


def _temp_git_paper(tmp_path: Path) -> tuple[Path, str]:
    paper = tmp_path / "paper"
    (paper / "r1" / "exam").mkdir(parents=True)
    shutil.copy2(ROOT / "r1" / "exam" / "campaign.py", paper / "r1" / "exam" / "campaign.py")
    env = {"GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
           "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.invalid"}
    subprocess.run(["git", "init", "-q", str(paper)], check=True, env=env)
    subprocess.run(["git", "-C", str(paper), "add", "r1/exam/campaign.py"], check=True, env=env)
    subprocess.run(["git", "-C", str(paper), "commit", "-q", "-m", "pinned"], check=True, env=env)
    head = subprocess.check_output(["git", "-C", str(paper), "rev-parse", "HEAD"], text=True).strip()
    return paper, head


def test_label_patch_applies_cleanly_records_both_shas_and_keeps_the_checkout_clean(tmp_path, monkeypatch):
    paper, head = _temp_git_paper(tmp_path)
    monkeypatch.setattr(replay, "PAPER_COMMIT", head)
    original_sha = sha((paper / replay.PATCH_TARGET).read_bytes())
    result = replay.apply_label_patch(paper, PATCH, tmp_path / "work_patch")
    assert result["applied_cleanly"] is True
    assert result["patch_sha256"] == replay.PATCH_SHA256
    assert result["original_source_sha256"] == original_sha
    assert result["patched_source_sha256"] != original_sha
    patched = Path(result["patched_campaign_source"]).read_text()
    assert "execution_label':'ENGINEERING_ONLY'" in patched
    assert "replay_marker':'s2_c3_replay/v1'" in patched
    assert "S2-C3 replay label patch refuses a DRYRUN job" in patched
    # the authorization checkout is untouched and clean
    assert sha((paper / replay.PATCH_TARGET).read_bytes()) == original_sha
    assert subprocess.check_output(["git", "-C", str(paper), "status", "--porcelain"], text=True) == ""
    scope = json.loads((tmp_path / "work_patch" / "LABEL_SCOPE.json").read_text())
    assert scope["original_source_sha256"] == original_sha
    assert scope["patched_source_sha256"] == result["patched_source_sha256"]
    assert scope["execution_label_only"] is True


def test_label_patch_refuses_a_dirty_authorization_checkout(tmp_path, monkeypatch):
    paper, head = _temp_git_paper(tmp_path)
    monkeypatch.setattr(replay, "PAPER_COMMIT", head)
    (paper / "untracked.txt").write_text("dirty\n")
    with pytest.raises(replay.Stop, match="not clean"):
        replay.apply_label_patch(paper, PATCH, tmp_path / "work_patch")


def test_label_patch_refuses_a_wrong_pin(tmp_path):
    paper, head = _temp_git_paper(tmp_path)
    tampered = tmp_path / "patch.diff"
    tampered.write_text(PATCH.read_text() + "\n")
    with pytest.raises(replay.Stop, match="sha256"):
        replay.apply_label_patch(paper, tampered, tmp_path / "work_patch")


# ------------------------------------------------------------------ authorization pre-flight
def _fake_cfg(tmp_path: Path, out: Path, *, work_dir: Path | None = None) -> dict:
    files = {}
    for key in ("rule", "stage_a_table", "stage_a_amendment_table", "stage_a_amendment_acceptance"):
        path = tmp_path / f"{key}.bin"
        path.write_bytes(key.encode())
        files[key] = {"path": str(path), "sha": sha(path.read_bytes())}
    return {"work_dir": str(work_dir or tmp_path / "work"), "models_dir": str(tmp_path / "models"),
            "rule": files["rule"]["path"], "rule_sha256": files["rule"]["sha"],
            "stage_a_table": files["stage_a_table"]["path"],
            "stage_a_table_sha256": files["stage_a_table"]["sha"],
            "stage_a_amendment_table": files["stage_a_amendment_table"]["path"],
            "stage_a_amendment_table_sha256": files["stage_a_amendment_table"]["sha"],
            "stage_a_amendment_acceptance": files["stage_a_amendment_acceptance"]["path"],
            "stage_a_amendment_acceptance_sha256": files["stage_a_amendment_acceptance"]["sha"]}


def test_preflight_blockers_enumerate_every_refusal(tmp_path):
    out = tmp_path / "work" / "out" / "digits_mlp__s9011"
    out.mkdir(parents=True)
    cfg = _fake_cfg(tmp_path, out)
    all_ok = {"checks": {name: {"ok": True} for name in
                         ("verify_b1_worker_input", "host_check", "require_worker_host", "harness_binding")}}
    assert replay.collect_preflight_blockers(SPEC, cfg, out, tmp_path, tmp_path, all_ok) == []
    failing = {"checks": {"verify_b1_worker_input": {"ok": False, "type": "RuntimeError", "error": "STOP: host"},
                          "host_check": {"ok": True}, "require_worker_host": {"ok": False,
                                                                            "type": "RuntimeError",
                                                                            "error": "STOP: host"},
                          "harness_binding": {"ok": True}}}
    blockers = replay.collect_preflight_blockers(SPEC, cfg, out, tmp_path, tmp_path, failing)
    assert {entry["gate"] for entry in blockers} == {"verify_b1_worker_input", "require_worker_host"}


def test_preflight_flags_the_out_rewrite_and_missing_authorization_inputs(tmp_path):
    out = tmp_path / "sandbox" / "digits_mlp__s9011"
    outside = tmp_path / "work"
    cfg = _fake_cfg(tmp_path, out, work_dir=outside)
    cfg["stage_a_table"] = str(tmp_path / "missing_table.json")
    all_ok = {"checks": {name: {"ok": True} for name in
                         ("verify_b1_worker_input", "host_check", "require_worker_host", "harness_binding")}}
    gates = {entry["gate"] for entry in replay.collect_preflight_blockers(SPEC, cfg, out, tmp_path, tmp_path,
                                                                          all_ok)}
    assert "out_under_work_dir" in gates
    assert "authorization_input:stage_a_table" in gates


def test_preflight_flags_a_missing_openml_cache_for_openml_nodes(tmp_path):
    spec = copy.deepcopy(SPEC)
    spec["node"] = "openml_ionosphere"
    spec["chunk_id"] = "openml_ionosphere"
    validated = replay.validate_spec(spec)
    out = tmp_path / "work" / "out" / "openml_ionosphere__s9011"
    out.mkdir(parents=True)
    cfg = _fake_cfg(tmp_path, out)
    all_ok = {"checks": {name: {"ok": True} for name in
                         ("verify_b1_worker_input", "host_check", "require_worker_host", "harness_binding")}}
    gates = {entry["gate"] for entry in replay.collect_preflight_blockers(validated["spec"], cfg, out,
                                                                          tmp_path, tmp_path, all_ok)}
    assert "openml_data_cache" in gates


GATE_NAMES = ("verify_b1_worker_input", "host_check", "require_worker_host", "harness_binding",
              "authorized_candidate")
assert set(GATE_NAMES) == set(replay.PROBE_GATES)


def _paper_stub(cwd: Path) -> None:
    """Stage the committed relative authorization inputs the blocker enumeration reads (rule + acceptance)."""
    paper = cwd / "paper"
    for rel, source in (("r1/exam/rules/x5_rule_v2.yaml", ROOT / "r1/exam/rules/x5_rule_v2.yaml"),
                        ("docs/r1/reports/OPS_O1_20261104.md", ROOT / "docs/r1/reports/OPS_O1_20261104.md")):
        target = paper / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
TASL_REFUSAL = {"verify_b1_worker_input": "STOP: stage_a_table", "host_check": "STOP: host",
                "require_worker_host": "STOP: host", "authorized_candidate": "STOP: TASL stage_a_table",
                "harness_binding": "OK"}


def _probe_result(names, ok_names, node="digits_mlp"):
    checks = {name: {"ok": name in ok_names} for name in names}
    for name, result in checks.items():
        if not result["ok"]:
            result["type"] = "FileNotFoundError" if name == "authorized_candidate" else "RuntimeError"
            result["error"] = TASL_REFUSAL.get(name, "STOP: refused")
    return {"probe_rc": 0, "checks": checks, "stderr_tail": ""}


def _tasl_probe_result(node="digits_mlp"):
    """The exact unshimmed TASL refusal set, as the real probe reports it (plus the non-probe blockers)."""
    return _probe_result(GATE_NAMES, {"harness_binding"})


def test_gate_probe_reports_each_campaign_gate(monkeypatch, tmp_path):
    seen = {"calls": []}

    def fake_probe(paper_dir, harness_dir, job_path, patched_campaign, patched_runtime, patched_runner,
                   env_extra=None):
        seen["job"] = json.loads(Path(job_path).read_text())
        seen["calls"].append(env_extra)
        if env_extra is None:  # the unshimmed TASL walk
            return _tasl_probe_result()
        return _probe_result(GATE_NAMES, set(GATE_NAMES))

    monkeypatch.setattr(replay, "run_gate_probe", fake_probe)
    _paper_stub(tmp_path)
    prepared = {"jobs": {root: json.loads((INPUTS / "digits_mlp__s9011" / "job.json").read_text())
                         for root in replay.ROOTS},
                "patch": {"patched_campaign_source": str(tmp_path / "campaign.patched.py"),
                          "patched_runtime_source": str(tmp_path / "runtime.patched.py"),
                          "patched_runner_source": str(tmp_path / "exam_runner.patched.py"),
                          "shim_scope": {"additions_only": True}}}
    result = replay.preflight(tmp_path, SPEC, prepared)
    assert result["status"] == "PASS"
    assert result["expected_tasl_blockers"] == sorted(replay.TASL_BLOCKER_GATES)
    assert result["missing_tasl_blockers"] == [] and result["unexpected_tasl_blockers"] == []
    assert result["shim_gate_names"] == sorted(GATE_NAMES)
    assert {entry["gate"] for entry in result["tasl_blockers"]} == replay.TASL_BLOCKER_GATES
    bypassed_gates = {entry["gate"] for entry in result["bypassed"]}
    assert {"verify_b1_worker_input", "host_check", "require_worker_host", "out_under_work_dir",
            "authorized_candidate"} <= bypassed_gates
    assert bypassed_gates == replay.TASL_BLOCKER_GATES
    assert all(entry["disposition"] != "NOT REVIEWED" for entry in result["bypassed"])
    assert len(seen["calls"]) == 2 and seen["calls"][0] is None and seen["calls"][1]
    assert set(seen["calls"][1]) == {replay.REPLAY_DECLARED_ENV, replay.REPLAY_ROOT_ENV,
                                     replay.REPLAY_SANDBOX_ENV}
    assert seen["job"]["out"].endswith("digits_mlp__s9011")


def test_preflight_requires_the_exact_unshimmed_refusal_set(monkeypatch, tmp_path):
    _paper_stub(tmp_path)
    prepared = {"jobs": {root: json.loads((INPUTS / "digits_mlp__s9011" / "job.json").read_text())
                         for root in replay.ROOTS},
                "patch": {"patched_campaign_source": str(tmp_path / "campaign.patched.py"),
                          "patched_runtime_source": str(tmp_path / "runtime.patched.py"),
                          "patched_runner_source": str(tmp_path / "exam_runner.patched.py"),
                          "shim_scope": {"additions_only": True}}}

    def subset_probe(paper_dir, harness_dir, job_path, patched_campaign, patched_runtime, patched_runner,
                     env_extra=None):
        # a gate that should refuse now passes: the set is no longer exactly the reviewed one -> STOP
        if env_extra is None:
            return _probe_result(GATE_NAMES, {"harness_binding", "host_check"})
        return _probe_result(GATE_NAMES, set(GATE_NAMES))

    monkeypatch.setattr(replay, "run_gate_probe", subset_probe)
    result = replay.preflight(tmp_path, SPEC, prepared)
    assert result["status"] == "STOP" and "host_check" in result["missing_tasl_blockers"]

    def extra_probe(paper_dir, harness_dir, job_path, patched_campaign, patched_runtime, patched_runner,
                    env_extra=None):
        # harness_binding is one of the five probe gates but is NOT expected to refuse in the TASL walk; if it
        # refuses, the environment is not the expected one -> an unexpected refusal (STOP, no silent bypass).
        if env_extra is None:
            return _probe_result(GATE_NAMES, set(GATE_NAMES) - {"harness_binding"})
        return _probe_result(GATE_NAMES, set(GATE_NAMES))

    monkeypatch.setattr(replay, "run_gate_probe", extra_probe)
    result = replay.preflight(tmp_path, SPEC, prepared)
    assert result["status"] == "STOP" and "harness_binding" in result["unexpected_tasl_blockers"]

    def failing_shim(paper_dir, harness_dir, job_path, patched_campaign, patched_runtime, patched_runner,
                     env_extra=None):
        if env_extra is None:
            return _tasl_probe_result()
        return _probe_result(GATE_NAMES, set(GATE_NAMES) - {"authorized_candidate"})

    monkeypatch.setattr(replay, "run_gate_probe", failing_shim)
    result = replay.preflight(tmp_path, SPEC, prepared)
    assert result["status"] == "STOP" and "authorized_candidate" in result["shim_failed"]


def _write_campaign_out(cwd: Path, node: str, seed: int, final_y: float, **over) -> dict:
    root = f"{node}__s{seed}"
    out = cwd / "out" / root
    out.mkdir(parents=True, exist_ok=True)
    job = json.loads((INPUTS / root / "job.json").read_text())
    job["out"] = str(out)
    job["base_url"] = "http://127.0.0.1:18130/v1"
    (out / "job.json").write_text(json.dumps(job, indent=2) + "\n")
    manifest = _campaign_manifest(node, seed, final_y, **over)
    manifest["job_sha256"] = sha((out / "job.json").read_bytes())
    (out / "campaign_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def test_campaign_manifest_validation_accepts_a_complete_replay_root(tmp_path):
    manifest = _write_campaign_out(tmp_path, "digits_mlp", 9011, 0.9727019)
    job = json.loads((tmp_path / "out" / "digits_mlp__s9011" / "job.json").read_text())
    checked = replay.validate_campaign_manifest(tmp_path / "out" / "digits_mlp__s9011", job,
                                                {"recomputed": replay.BINDING}, SPEC)
    assert checked["execution_label"] == replay.LABEL and checked["audit_seeds"] == list(replay.AUDIT_SEEDS)


def test_campaign_manifest_validation_refuses_label_leak_seeds_and_missing_manifest(tmp_path):
    out = tmp_path / "out" / "digits_mlp__s9011"
    job = json.loads((INPUTS / "digits_mlp__s9011" / "job.json").read_text())
    job["out"] = str(out)
    with pytest.raises(replay.Stop, match="campaign_manifest"):
        replay.validate_campaign_manifest(out, job, {"recomputed": replay.BINDING}, SPEC)
    manifest = _write_campaign_out(tmp_path, "digits_mlp", 9011, 0.9727019)
    manifest["execution_label"] = "EVIDENCE"
    (out / "campaign_manifest.json").write_text(json.dumps(manifest) + "\n")
    with pytest.raises(replay.Stop, match="label leak"):
        replay.validate_campaign_manifest(out, job, {"recomputed": replay.BINDING}, SPEC)
    manifest = _write_campaign_out(tmp_path, "digits_mlp", 9011, 0.9727019)
    manifest["final_audits"][0]["seeds"] = list(range(7001, 7011))
    (out / "campaign_manifest.json").write_text(json.dumps(manifest) + "\n")
    with pytest.raises(replay.Stop, match="7001-7010|final-audit seeds"):
        replay.validate_campaign_manifest(out, job, {"recomputed": replay.BINDING}, SPEC)


def test_scan_forbidden_b2_audit_seeds_is_recursive():
    replay._scan_forbidden_seeds({"seeds": list(replay.AUDIT_SEEDS)})
    replay._scan_forbidden_seeds({"a": [{"b": {"audit_seeds": [9201, 9202]}}]})
    with pytest.raises(replay.Stop, match="7001-7010"):
        replay._scan_forbidden_seeds({"a": [{"b": {"seeds": [9201, 7005]}}]})


# ------------------------------------------------------------------ comparison maths (tolerance boundaries)
def _collected(final_y: dict | None = None, diagnostics: dict | None = None,
               server: tuple[int, int] = (61, 61), per_job_wall=(1000.0, 1000.0, 1000.0)) -> dict:
    instances = {}
    for root in replay.ROOTS:
        instances[root] = {"final_y": (final_y or compare.EXPECTED_FINAL_Y)[root],
                           "diagnostics": (diagnostics or {}).get(root, {})}
    outputs = []
    for index, node in enumerate(replay.NODES):
        outputs.append({"record": {"node": node, "status": "COMPLETE"},
                        "server": {"offloaded_layers": server[0], "total_layers": server[1]},
                        "log_offload": {"offloaded_layers": server[0], "total_layers": server[1]},
                        "wall_s": per_job_wall[index]})
    return {"instances": instances, "outputs": outputs}


def _diag(**over) -> dict:
    base = {"trials": 240, "evaluated": 240, "invalid": 20, "duplicates": 33, "noops": 20,
            "parse_failed": 0, "forecast_queries": 240, "forecast_query_failed": 0}
    base.update(over)
    return {"digits_mlp__s9011": base}


def test_criteria_all_pass_baseline():
    results = compare.apply_criteria(_collected(diagnostics=_diag()))
    assert results["overall_pass"] is True
    for key in ("1_final_y", "2_parse_failures", "3_diagnostics", "4_full_offload", "5_throughput",
                "6_no_stop"):
        assert results[key]["pass"] is True, key


def test_criterion1_boundaries():
    final_y = dict(compare.EXPECTED_FINAL_Y)
    final_y["digits_mlp__s9011"] = compare.EXPECTED_FINAL_Y["digits_mlp__s9011"] + 0.02
    assert compare.apply_criteria(_collected(final_y=final_y, diagnostics=_diag()))["1_final_y"]["pass"] is True
    final_y["digits_mlp__s9011"] = compare.EXPECTED_FINAL_Y["digits_mlp__s9011"] + 0.0200001
    assert compare.apply_criteria(_collected(final_y=final_y, diagnostics=_diag()))["1_final_y"]["pass"] is False


def test_criterion1_mean_boundary():
    final_y = {root: compare.EXPECTED_FINAL_Y[root] + 0.01 for root in replay.ROOTS}
    results = compare.apply_criteria(_collected(final_y=final_y, diagnostics=_diag()))
    assert results["1_final_y"]["mean_abs_delta"] == pytest.approx(0.01, abs=1e-9)
    assert results["1_final_y"]["pass"] is True
    final_y["digits_mlp__s9011"] += 0.001  # mean 0.0100833 > 0.01
    assert compare.apply_criteria(_collected(final_y=final_y, diagnostics=_diag()))["1_final_y"]["pass"] is False


def test_criterion2_parse_rate_boundary():
    assert compare.apply_criteria(_collected(diagnostics=_diag(parse_failed=2, forecast_queries=100)))[
        "2_parse_failures"]["pass"] is True
    assert compare.apply_criteria(_collected(diagnostics=_diag(parse_failed=3, forecast_queries=100)))[
        "2_parse_failures"]["pass"] is False
    assert compare.apply_criteria(_collected(diagnostics=_diag(parse_failed=0, forecast_queries=0)))[
        "2_parse_failures"]["pass"] is False


def test_criterion3_plus_minus_ten_percent_boundaries():
    cases = ((20, 22, True), (20, 23, False), (33, 36, True), (33, 37, False))
    for expected_key, observed, expected_pass in cases:
        key = {20: "invalid", 33: "duplicates"}[expected_key]
        results = compare.apply_criteria(_collected(diagnostics=_diag(**{key: observed})))
        assert results["3_diagnostics"]["values"][key]["observed"] == observed
        assert results["3_diagnostics"]["values"][key]["within_declared"] is expected_pass
        assert results["3_diagnostics"]["pass"] is expected_pass
    assert compare.apply_criteria(_collected(diagnostics=_diag(noops=22)))["3_diagnostics"]["pass"] is True
    assert compare.apply_criteria(_collected(diagnostics=_diag(noops=64)))["3_diagnostics"]["pass"] is False


def test_criterion3_pre_data_correction_is_applied():
    results = compare.apply_criteria(_collected(diagnostics=_diag()))
    assert results["3_diagnostics"]["declared_denominator_defect"] is False
    assert compare.EXPECTED_DIAG_DECLARED == {"invalid": 20, "duplicates": 33, "noops": 20}
    assert compare.EXPECTED_DIAG_DECLARED_ORIGINAL == {"invalid": 58, "duplicates": 82, "noops": 58}
    sources = compare.verify_expected_sources(ROOT)
    assert sources["criterion3_denominator_defect"] is False


def test_criterion4_offload_boundaries():
    assert compare.apply_criteria(_collected(diagnostics=_diag(), server=(61, 61)))["4_full_offload"]["pass"] is True
    assert compare.apply_criteria(_collected(diagnostics=_diag(), server=(60, 61)))["4_full_offload"]["pass"] is False
    assert compare.apply_criteria(_collected(diagnostics=_diag(), server=(60, 60)))["4_full_offload"]["pass"] is False


def test_criterion5_throughput_boundary():
    limit = 2 * compare.B2_GPU_HOURS_OFF * 3600
    assert compare.apply_criteria(_collected(diagnostics=_diag(), per_job_wall=(limit, 0, 0)))[
        "5_throughput"]["pass"] is True
    assert compare.apply_criteria(_collected(diagnostics=_diag(), per_job_wall=(limit + 1, 0, 0)))[
        "5_throughput"]["pass"] is False


def test_expected_sources_pin_is_checked():
    assert compare.verify_expected_sources(ROOT)["criteria_sha256"] == replay.CRITERIA_SHA256
    original = compare.EXPECTED_SOURCE_SHA256
    compare.EXPECTED_SOURCE_SHA256 = "0" * 64
    try:
        with pytest.raises(compare.Stop, match="criteria document"):
            compare.verify_expected_sources(ROOT)
    finally:
        compare.EXPECTED_SOURCE_SHA256 = original


# ------------------------------------------------------------------ comparison hard STOPs on real job outputs
def _campaign_manifest(node: str, seed: int, final_y: float, **over) -> dict:
    manifest = {"status": "COMPLETE", "label": "EXAM", "phase": "b2", "mode": "off", "candidate": "gemma4_31b",
                "node": node, "instance_seed": seed, "execution_label": replay.LABEL,
                "replay_marker": replay.REPLAY_MARKER, "job_binding": replay.BINDING,
                "diagnostics": {"trials": 20, "evaluated": 20, "invalid": 0, "duplicates": 0, "noops": 0,
                                "parse_failed": 0, "forecast_queries": 20, "forecast_query_failed": 0},
                "final_audits": [{"instance_id": f"{node}__s{seed}", "node": node,
                                  "seeds": list(replay.AUDIT_SEEDS), "metrics": [final_y] * 10,
                                  "final_y": final_y}]}
    manifest.update(over)
    return manifest


def _write_campaign_out(cwd: Path, node: str, seed: int, final_y: float, **over) -> dict:
    root = f"{node}__s{seed}"
    out = cwd / "out" / root
    out.mkdir(parents=True, exist_ok=True)
    job = json.loads((INPUTS / root / "job.json").read_text())
    job["out"] = str(out)
    job["base_url"] = "http://127.0.0.1:18130/v1"
    (out / "job.json").write_text(json.dumps(job, indent=2) + "\n")
    manifest = _campaign_manifest(node, seed, final_y, **over)
    manifest["job_sha256"] = sha((out / "job.json").read_bytes())
    (out / "campaign_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def test_campaign_manifest_validation_accepts_a_complete_replay_root(tmp_path):
    manifest = _write_campaign_out(tmp_path, "digits_mlp", 9011, 0.9727019)
    job = json.loads((tmp_path / "out" / "digits_mlp__s9011" / "job.json").read_text())
    checked = replay.validate_campaign_manifest(tmp_path / "out" / "digits_mlp__s9011", job,
                                                {"recomputed": replay.BINDING}, SPEC)
    assert checked["execution_label"] == replay.LABEL and checked["audit_seeds"] == list(replay.AUDIT_SEEDS)


def test_campaign_manifest_validation_refuses_label_leak_seeds_and_missing_manifest(tmp_path):
    out = tmp_path / "out" / "digits_mlp__s9011"
    job = json.loads((INPUTS / "digits_mlp__s9011" / "job.json").read_text())
    job["out"] = str(out)
    with pytest.raises(replay.Stop, match="campaign_manifest"):
        replay.validate_campaign_manifest(out, job, {"recomputed": replay.BINDING}, SPEC)
    manifest = _write_campaign_out(tmp_path, "digits_mlp", 9011, 0.9727019)
    manifest["execution_label"] = "EVIDENCE"
    (out / "campaign_manifest.json").write_text(json.dumps(manifest) + "\n")
    with pytest.raises(replay.Stop, match="label leak"):
        replay.validate_campaign_manifest(out, job, {"recomputed": replay.BINDING}, SPEC)
    manifest = _write_campaign_out(tmp_path, "digits_mlp", 9011, 0.9727019)
    manifest["final_audits"][0]["seeds"] = list(range(7001, 7011))
    (out / "campaign_manifest.json").write_text(json.dumps(manifest) + "\n")
    with pytest.raises(replay.Stop, match="7001-7010|final-audit seeds"):
        replay.validate_campaign_manifest(out, job, {"recomputed": replay.BINDING}, SPEC)


def test_scan_forbidden_b2_audit_seeds_is_recursive():
    replay._scan_forbidden_seeds({"seeds": list(replay.AUDIT_SEEDS)})
    replay._scan_forbidden_seeds({"a": [{"b": {"audit_seeds": [9201, 9202]}}]})
    with pytest.raises(replay.Stop, match="7001-7010"):
        replay._scan_forbidden_seeds({"a": [{"b": {"seeds": [9201, 7005]}}]})


# ------------------------------------------------------------------ comparison maths (tolerance boundaries)
def _collected(final_y: dict | None = None, diagnostics: dict | None = None,
               server: tuple[int, int] = (61, 61), per_job_wall=(1000.0, 1000.0, 1000.0)) -> dict:
    instances = {}
    for root in replay.ROOTS:
        instances[root] = {"final_y": (final_y or compare.EXPECTED_FINAL_Y)[root],
                           "diagnostics": (diagnostics or {}).get(root, {})}
    outputs = []
    for index, node in enumerate(replay.NODES):
        outputs.append({"record": {"node": node, "status": "COMPLETE"},
                        "server": {"offloaded_layers": server[0], "total_layers": server[1]},
                        "log_offload": {"offloaded_layers": server[0], "total_layers": server[1]},
                        "wall_s": per_job_wall[index]})
    return {"instances": instances, "outputs": outputs}


def _diag(**over) -> dict:
    base = {"trials": 240, "evaluated": 240, "invalid": 20, "duplicates": 33, "noops": 20,
            "parse_failed": 0, "forecast_queries": 240, "forecast_query_failed": 0}
    base.update(over)
    return {"digits_mlp__s9011": base}


def test_criteria_all_pass_baseline():
    results = compare.apply_criteria(_collected(diagnostics=_diag()))
    assert results["overall_pass"] is True
    for key in ("1_final_y", "2_parse_failures", "3_diagnostics", "4_full_offload", "5_throughput",
                "6_no_stop"):
        assert results[key]["pass"] is True, key


def test_criterion1_boundaries():
    final_y = dict(compare.EXPECTED_FINAL_Y)
    final_y["digits_mlp__s9011"] = compare.EXPECTED_FINAL_Y["digits_mlp__s9011"] + 0.02
    assert compare.apply_criteria(_collected(final_y=final_y, diagnostics=_diag()))["1_final_y"]["pass"] is True
    final_y["digits_mlp__s9011"] = compare.EXPECTED_FINAL_Y["digits_mlp__s9011"] + 0.0200001
    assert compare.apply_criteria(_collected(final_y=final_y, diagnostics=_diag()))["1_final_y"]["pass"] is False


def test_criterion1_mean_boundary():
    final_y = {root: compare.EXPECTED_FINAL_Y[root] + 0.01 for root in replay.ROOTS}
    results = compare.apply_criteria(_collected(final_y=final_y, diagnostics=_diag()))
    assert results["1_final_y"]["mean_abs_delta"] == pytest.approx(0.01, abs=1e-9)
    assert results["1_final_y"]["pass"] is True
    final_y["digits_mlp__s9011"] += 0.001  # mean 0.0100833 > 0.01
    assert compare.apply_criteria(_collected(final_y=final_y, diagnostics=_diag()))["1_final_y"]["pass"] is False


def test_criterion2_parse_rate_boundary():
    assert compare.apply_criteria(_collected(diagnostics=_diag(parse_failed=2, forecast_queries=100)))[
        "2_parse_failures"]["pass"] is True
    assert compare.apply_criteria(_collected(diagnostics=_diag(parse_failed=3, forecast_queries=100)))[
        "2_parse_failures"]["pass"] is False
    assert compare.apply_criteria(_collected(diagnostics=_diag(parse_failed=0, forecast_queries=0)))[
        "2_parse_failures"]["pass"] is False


def test_criterion3_plus_minus_ten_percent_boundaries():
    cases = ((20, 22, True), (20, 23, False), (33, 36, True), (33, 37, False))
    for expected_key, observed, expected_pass in cases:
        key = {20: "invalid", 33: "duplicates"}[expected_key]
        results = compare.apply_criteria(_collected(diagnostics=_diag(**{key: observed})))
        assert results["3_diagnostics"]["values"][key]["observed"] == observed
        assert results["3_diagnostics"]["values"][key]["within_declared"] is expected_pass
        assert results["3_diagnostics"]["pass"] is expected_pass
    assert compare.apply_criteria(_collected(diagnostics=_diag(noops=22)))["3_diagnostics"]["pass"] is True
    assert compare.apply_criteria(_collected(diagnostics=_diag(noops=64)))["3_diagnostics"]["pass"] is False


def test_criterion3_pre_data_correction_is_applied():
    results = compare.apply_criteria(_collected(diagnostics=_diag()))
    assert results["3_diagnostics"]["declared_denominator_defect"] is False
    assert compare.EXPECTED_DIAG_DECLARED == {"invalid": 20, "duplicates": 33, "noops": 20}
    assert compare.EXPECTED_DIAG_DECLARED_ORIGINAL == {"invalid": 58, "duplicates": 82, "noops": 58}
    sources = compare.verify_expected_sources(ROOT)
    assert sources["criterion3_denominator_defect"] is False


def test_criterion4_offload_boundaries():
    assert compare.apply_criteria(_collected(diagnostics=_diag(), server=(61, 61)))["4_full_offload"]["pass"] is True
    assert compare.apply_criteria(_collected(diagnostics=_diag(), server=(60, 61)))["4_full_offload"]["pass"] is False
    assert compare.apply_criteria(_collected(diagnostics=_diag(), server=(60, 60)))["4_full_offload"]["pass"] is False


def test_criterion5_throughput_boundary():
    limit = 2 * compare.B2_GPU_HOURS_OFF * 3600
    assert compare.apply_criteria(_collected(diagnostics=_diag(), per_job_wall=(limit, 0, 0)))[
        "5_throughput"]["pass"] is True
    assert compare.apply_criteria(_collected(diagnostics=_diag(), per_job_wall=(limit + 1, 0, 0)))[
        "5_throughput"]["pass"] is False


def test_expected_sources_pin_is_checked():
    assert compare.verify_expected_sources(ROOT)["criteria_sha256"] == replay.CRITERIA_SHA256
    original = compare.EXPECTED_SOURCE_SHA256
    compare.EXPECTED_SOURCE_SHA256 = "0" * 64
    try:
        with pytest.raises(compare.Stop, match="criteria document"):
            compare.verify_expected_sources(ROOT)
    finally:
        compare.EXPECTED_SOURCE_SHA256 = original


# ------------------------------------------------------------------ comparison hard STOPs on real job outputs
def _fake_job_output(base: Path, node: str, *, final_y=None, manifest_over=None, seed_over=None,
                     record_over=None, drop=(), duplicate=False) -> Path:
    chunk = base / f"job_{node}"
    chunk.mkdir(parents=True)
    record = {"schema": replay.RECORD_SCHEMA, "kind": replay.KIND, "run_id": "s2c3-test", "chunk_id": node,
              "node": node, "label": replay.LABEL, "replay_marker": replay.REPLAY_MARKER,
              "paper_commit": replay.PAPER_COMMIT, "harness_commit": replay.HARNESS_COMMIT,
              "image_digest": replay.IMAGE_DIGEST, "model_sha256": replay.GGUF_SHA256,
              "binding": {"recorded": replay.BINDING, "recomputed": replay.BINDING,
                          "unchanged_by_rewrite": True},
              "label_patch": {"patch_sha256": replay.PATCH_SHA256}, "status": "COMPLETE", "wall_s": 1000.0,
              "driver_shim": {"patch_sha256": replay.SHIM_SHA256, "targets": list(replay.SHIM_TARGETS),
                              "patched_source_sha256": replay.PATCHED_SOURCE_SHA256},
              "declared_inputs": {"manifest_sha256": replay.DECLARED_SHA256, "items_declared": 25,
                                  "items_verified": 25, "independent_of_tasl": True},
              "server": {"pid": 1, "base_url": "http://127.0.0.1:18130/v1", "build": "x",
                         "offloaded_layers": 61, "total_layers": 61,
                         "argv": ["llama-server", "-m", "model.gguf", "-c", "32768", "-ngl", "999", "-np", "1"],
                         "manager_settings": {"ctx": 32768, "n_gpu_layers": 999, "parallel": 1,
                                              "thinking": False, "cache_prompt": False,
                                              "cache_type_k": "q8_0", "cache_type_v": "q8_0"}},
              "roots": [{"instance_id": f"{node}__s{seed}", "returncode": 0, "wall_s": 250.0}
                        for seed in replay.SEEDS]}
    record.update(record_over or {})
    (chunk / "job_record.json").write_text(json.dumps(record, indent=1) + "\n")
    (chunk / "llama-server.log").write_text("load_tensors: offloaded 61/61 layers to GPU\nCUDA0 model buffer size = 1 MiB\n")
    for seed in replay.SEEDS:
        root = f"{node}__s{seed}"
        if root in drop:
            continue
        out = chunk / "out" / root
        out.mkdir(parents=True)
        job = json.loads((INPUTS / root / "job.json").read_text())
        job["out"] = str(out)
        (out / "job.json").write_text(json.dumps(job, indent=2) + "\n")
        value = (final_y or compare.EXPECTED_FINAL_Y)[root]
        over = dict(manifest_over or {})
        over.update((seed_over or {}).get(seed, {}))
        manifest = _campaign_manifest(node, seed, value, **over)
        manifest["job_sha256"] = sha((out / "job.json").read_bytes())
        (out / "campaign_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if duplicate:
        extra = chunk / "out" / "duplicate"
        extra.mkdir(parents=True)
        manifest = _campaign_manifest(node, replay.SEEDS[0], 0.9)
        manifest["job_sha256"] = "0" * 64
        (extra / "campaign_manifest.json").write_text(json.dumps(manifest) + "\n")
    return chunk


def _three_outputs(base: Path, **overrides) -> list[Path]:
    chunks = []
    for node in replay.NODES:
        chunks.append(_fake_job_output(base, node, **overrides.get(node, {})))
    return chunks


def test_compare_passes_on_matching_synthetic_outputs(tmp_path):
    sources = compare.verify_expected_sources(ROOT)
    diag = {"trials": 240, "evaluated": 240, "invalid": 20, "duplicates": 33, "noops": 20,
            "parse_failed": 0, "forecast_queries": 240, "forecast_query_failed": 0}
    chunk = _fake_job_output(tmp_path / "jobs", "digits_mlp", seed_over={9011: {"diagnostics": diag}})
    from_openml = [_fake_job_output(tmp_path / "jobs", node) for node in replay.NODES[1:]]
    collected = compare.collect([chunk, *from_openml])
    results = compare.apply_criteria(collected)
    assert results["overall_pass"] is True
    report = tmp_path / "S2_C3_RESULTS.md"
    text = compare.write_report(collected, results, sources, report)
    assert report.is_file()
    assert "**Verdict: PASS**" in text
    for root in replay.ROOTS:
        assert root in text
    assert "20/33/20" in text or "criterion 3" in text


def test_compare_math_failures_give_not_pass_not_stop(tmp_path):
    final_y = dict(compare.EXPECTED_FINAL_Y)
    final_y["digits_mlp__s9011"] += 0.05
    chunks = _three_outputs(tmp_path / "jobs", digits_mlp={"final_y": final_y})
    collected = compare.collect(chunks)
    results = compare.apply_criteria(collected)
    assert results["overall_pass"] is False and results["1_final_y"]["pass"] is False
    text = compare.write_report(collected, results, compare.verify_expected_sources(ROOT),
                                tmp_path / "S2_C3_RESULTS.md")
    assert "**Verdict: NOT PASS**" in text


def test_compare_hard_stop_missing_instance(tmp_path):
    chunks = _three_outputs(tmp_path / "jobs", digits_mlp={"drop": ("digits_mlp__s9011",)})
    with pytest.raises(compare.Stop, match="does not cover exactly"):
        compare.collect(chunks)


def test_compare_hard_stop_duplicate_instance(tmp_path):
    chunks = _three_outputs(tmp_path / "jobs", digits_mlp={"duplicate": True})
    with pytest.raises(compare.Stop, match="duplicate"):
        compare.collect(chunks)


def test_compare_hard_stop_label_leak(tmp_path):
    chunks = _three_outputs(tmp_path / "jobs", digits_mlp={"manifest_over": {"execution_label": "EVIDENCE"}})
    with pytest.raises(compare.Stop, match="label leak"):
        compare.collect(chunks)


def test_compare_hard_stop_pin_mismatch(tmp_path):
    chunks = _three_outputs(tmp_path / "jobs", openml_ionosphere={"record_over": {"harness_commit": "0" * 40}})
    with pytest.raises(compare.Stop, match="pin harness_commit"):
        compare.collect(chunks)


def test_compare_hard_stop_audit_seed_mismatch(tmp_path):
    bad = {"final_audits": [{"instance_id": "x"}]}  # overwritten per root below
    manifest_over = {}
    chunks = _three_outputs(tmp_path / "jobs")
    target = tmp_path / "jobs" / "job_digits_mlp" / "out" / "digits_mlp__s9011" / "campaign_manifest.json"
    manifest = json.loads(target.read_text())
    manifest["final_audits"][0]["seeds"] = list(range(9101, 9111))
    target.write_text(json.dumps(manifest) + "\n")
    with pytest.raises(compare.Stop, match="seeds"):
        compare.collect(chunks)


def test_compare_hard_stop_unreadable_job_output(tmp_path):
    chunk = tmp_path / "jobs" / "job_digits_mlp"
    chunk.mkdir(parents=True)
    with pytest.raises(compare.Stop, match="job_record"):
        compare.collect([chunk, tmp_path / "missing1", tmp_path / "missing2"])


def test_compare_hard_stop_missing_shim_declared_or_server_pins(tmp_path):
    chips = _three_outputs(tmp_path / "jobs")
    record_path = chips[0] / "job_record.json"
    original = json.loads(record_path.read_text())
    for mutate, match in (
            (lambda r: r.pop("driver_shim"), "driver-shim"),
            (lambda r: r["driver_shim"].__setitem__("patch_sha256", "0" * 64), "driver-shim"),
            (lambda r: r["driver_shim"].__setitem__("patched_source_sha256", {}), "patched-source"),
            (lambda r: r["declared_inputs"].__setitem__("manifest_sha256", "0" * 64), "declared-inputs"),
            (lambda r: r["declared_inputs"].__setitem__("items_verified", 24), "every declared input"),
            (lambda r: r["server"].pop("argv"), "lacks argv"),
            (lambda r: r["server"].__setitem__("manager_settings", {}), "manager setting")):
        record = copy.deepcopy(original)
        mutate(record)
        record_path.write_text(json.dumps(record, indent=1) + "\n")
        with pytest.raises(compare.Stop, match=match):
            compare.load_job_output(chips[0])
    record_path.write_text(json.dumps(original, indent=1) + "\n")


def test_compare_hard_stop_job_sha_not_binding_its_job_json(tmp_path):
    chunks = _three_outputs(tmp_path / "jobs")
    target = chunks[0] / "out" / "digits_mlp__s9011" / "campaign_manifest.json"
    manifest = json.loads(target.read_text())
    manifest["job_sha256"] = "0" * 64
    target.write_text(json.dumps(manifest) + "\n")
    with pytest.raises(compare.Stop, match="job_sha256"):
        compare.collect(chunks)


# ------------------------------------------------------------------ renderer + job entry + record + seal
def test_renderer_renders_the_replay_jdl_and_stages_the_pinned_inputs(tmp_path):
    out = tmp_path / "replay.jdl"
    stage = tmp_path / "stage"
    render_jdl.main([str(ROOT / "sweep2" / "spec.replay.example.json"), "--out", str(out),
                     "--stage-dir", str(stage)])
    jdl = out.read_text()
    assert "executable = s2_c3_replay_job.sh" in jdl and "arguments = s2_c3_spec.json" in jdl
    assert "universe = container" in jdl
    assert "container_image = docker://ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35" in jdl
    assert "TARGET.GPUs_GlobalMemoryMb >= 24576" in jdl and "TARGET.GPUs_Capability >= 7.0" in jdl
    assert 'TARGET.GPUs_DeviceName =?= "NVIDIA H200"' in jdl  # diagnostic same-GPU repeat
    assert "TARGET.CloudSite" not in jdl
    assert "TARGET.CpuFamily" not in jdl and "TARGET.CpuModelNumber" not in jdl
    # R1-SWEEP2-LAYOUT: the author-accepted 32k layout comes from the spec, never from a hard-coded default
    assert "request_disk = 42460970" in jdl and "request_memory = 32000" in jdl
    assert "+RequestWalltime = 8735" in jdl
    assert "request_disk = 50000000" not in jdl and "request_memory = 128000" not in jdl
    assert "+RemoteJob = True" in jdl
    assert "transfer_output_files = out.tar,work.tar,job_record.json,SHA256SUMS,llama-server.log" in jdl
    assert "ProvidesEtpCeph" not in jdl and "docker_image" not in jdl
    assert "s2_c3_label_patch.diff" in jdl and "S2_C3_CRITERIA.md" in jdl
    assert "s2_c3_driver_shim.diff" in jdl and "S2C3_IN_DECLARED.json" in jdl
    assert "S2C3_IN_stage_a_table_t7h8.json" in jdl and "S2C3_IN_stage_a_amendment_table_t7j10.json" in jdl
    assert "S2C3_IN_prompts.jsonl" in jdl and "S2C3_IN_openml_cache.tar.gz" in jdl
    assert "S2C3_IN_digits_mlp__s9011_job.json" in jdl
    assert len([p for p in stage.iterdir() if p.is_file()]) == 37
    staged = json.loads((stage / "s2_c3_spec.json").read_text())
    assert staged["schema"] == replay.SCHEMA


def test_renderer_refuses_a_tampered_replay_spec(tmp_path):
    spec = spec_copy()
    spec["image"]["digest"] = "ghcr.io/other@sha256:" + "0" * 64
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec))
    with pytest.raises(replay.Stop):
        render_jdl.main([str(path), "--out", str(tmp_path / "x.jdl"), "--stage-dir", str(tmp_path / "stage")])


def test_renderer_still_renders_the_c2_spec(tmp_path):
    out = tmp_path / "c2.jdl"
    render_jdl.main([str(ROOT / "sweep2" / "spec.example.json"), "--out", str(out),
                     "--stage-dir", str(tmp_path / "stage")])
    jdl = out.read_text()
    assert "executable = s2_c2_job.sh" in jdl and "arguments = s2_c2_spec.json" in jdl
    assert "s2_c2_job.sh,s2_c2_lib.py,s2_c2_spec.json" in jdl
    assert "request_disk = 42460970" in jdl and "request_memory = 32000" in jdl
    assert "+RequestWalltime = 8735" in jdl


def test_renderer_refuses_a_spec_without_the_accepted_layout(tmp_path):
    spec = json.loads((ROOT / "sweep2" / "spec.replay.example.json").read_text())
    for key in ("walltime_s", "request_disk_kb", "request_memory_mb"):
        broken = copy.deepcopy(spec)
        del broken[key]
        path = tmp_path / f"spec_no_{key}.json"
        path.write_text(json.dumps(broken))
        with pytest.raises(replay.Stop, match=key):
            render_jdl.main([str(path), "--out", str(tmp_path / f"{key}.jdl"),
                             "--stage-dir", str(tmp_path / f"stage_{key}")])


def test_replay_job_entry_precreates_the_transferred_outputs():
    text = (ROOT / "sweep2" / "s2_c3_replay_job.sh").read_text()
    for name in ("out.tar", "work.tar", "job_record.json", "SHA256SUMS", "llama-server.log"):
        assert name in text
    assert "s2_c3_replay.py" in text and "run" in text


def test_record_base_is_engineering_only_and_carries_no_b2_audit():
    record = replay._record_base(SPEC, {"recomputed": replay.BINDING},
                                 [{"root": "digits_mlp__s9011"}],
                                 {"patch_sha256": replay.PATCH_SHA256})
    assert record["schema"] == replay.RECORD_SCHEMA and record["label"] == replay.LABEL
    assert record["replay_marker"] == replay.REPLAY_MARKER
    assert record["audit_seeds"] == list(replay.AUDIT_SEEDS)
    assert "none" in record["b2_audits"] and "7001-7010" in record["b2_audits"]
    assert "ENGINEERING" in record["output_use"]


def test_layout_is_the_author_accepted_32k_set_and_the_timeout_derives_from_it():
    assert (replay.WALLTIME_S, replay.REQUEST_DISK_KB, replay.REQUEST_MEMORY_MB) == (8735, 42460970, 32000)
    assert replay.root_timeout_s(SPEC) == 8135
    layout = replay.layout_record(SPEC)
    assert layout["walltime_s"] == 8735 and layout["request_disk_kb"] == 42460970
    assert layout["request_memory_mb"] == 32000 and layout["per_root_timeout_s"] == 8135
    record = replay._record_base(SPEC, {"recomputed": replay.BINDING}, [], {"patch_sha256": replay.PATCH_SHA256})
    assert record["layout"] == layout


def test_record_base_notes_the_external_authority_row():
    record = replay._record_base(SPEC, {"recomputed": replay.BINDING}, [], {"patch_sha256": replay.PATCH_SHA256})
    authority = record["authority"]
    assert authority["row"] == "R1-S2C3-DRIVER" and authority["commit"].startswith("025bfc16")
    assert authority["branch_ancestor"] is False and "merge-base 9ae6d877" in authority["ancestry_note"]


def test_server_record_carries_the_started_argv_and_the_pinned_manager_settings():
    server = {"pid": 7, "base_url": "http://127.0.0.1:18130/v1", "build": "0.7.0-dev (build 11669, commit 620d2225c)",
              "offloaded_layers": 61, "total_layers": 61, "cuda_lines": ["CUDA0 model buffer size = 1 MiB"],
              "log": "/tmp/x.log", "argv": ["/opt/r1/llama/bin/llama-server", "-m", "model.gguf", "-c", "32768"]}
    record = replay.server_record(SPEC, server)
    assert record["argv"] == server["argv"]
    settings = record["manager_settings"]
    assert settings["ctx"] == 32768 and settings["n_gpu_layers"] == 999 and settings["parallel"] == 1
    assert settings["cache_prompt"] is False and settings["thinking"] is False
    assert settings["cache_type_k"] == "q8_0" and settings["cache_type_v"] == "q8_0"
    assert settings["jinja"] is True and settings["alias"] == "gemma4_31b"


def _sealable_output(tmp_path: Path) -> Path:
    chunk = tmp_path / "job_digits_mlp"
    chunk.mkdir()
    record = {"schema": replay.RECORD_SCHEMA, "kind": replay.KIND, "run_id": "s2c3-seal-test",
              "chunk_id": "digits_mlp", "node": "digits_mlp", "label": replay.LABEL,
              "replay_marker": replay.REPLAY_MARKER, "image_digest": replay.IMAGE_DIGEST,
              "model_sha256": replay.GGUF_SHA256, "paper_commit": replay.PAPER_COMMIT,
              "harness_commit": replay.HARNESS_COMMIT, "label_patch": {"patch_sha256": replay.PATCH_SHA256},
              "driver_shim": {"patch_sha256": replay.SHIM_SHA256,
                              "patched_source_sha256": replay.PATCHED_SOURCE_SHA256},
              "declared_inputs": {"manifest_sha256": replay.DECLARED_SHA256, "items_declared": 25,
                                  "items_verified": 25, "independent_of_tasl": True},
              "host": {"fqdn": "g3605.nemo.privat", "hostname": "g3605"},
              "status": "COMPLETE"}
    (chunk / "job_record.json").write_text(json.dumps(record, indent=1) + "\n")
    (chunk / "llama-server.log").write_text("load_tensors: offloaded 61/61 layers to GPU\n")
    for name in ("out", "work"):
        src = chunk / name
        src.mkdir()
        (src / "x.txt").write_text(name + "\n")
        replay.lib._tar_dir(src, chunk / f"{name}.tar")
    lib._write_sums(chunk)
    return chunk


def test_seal_writes_the_engineering_only_marker_and_guards_reuse_the_c2_machinery(tmp_path, monkeypatch):
    sealed_root = tmp_path / "sealed"
    sealed_root.mkdir()
    monkeypatch.setattr(lib, "SEALED_ROOT", sealed_root)
    chunk = _sealable_output(tmp_path)
    receipt = replay.seal_replay(chunk, "s2c3-seal-test", "digits_mlp")
    target = sealed_root / "s2c3-seal-test" / "digits_mlp"
    assert Path(receipt["sealed_path"]) == target
    assert (target / "ENGINEERING_ONLY.txt").is_file()
    assert (target / "SEAL_RECEIPT.json").is_file() and (target / "SHA256SUMS").is_file()
    assert receipt["label"] == replay.LABEL and receipt["label_patch_sha256"] == replay.PATCH_SHA256
    assert "ENGINEERING_ONLY" in (target / "ENGINEERING_ONLY.txt").read_text()
    # no overwrite
    with pytest.raises(replay.Stop, match="no overwrite"):
        replay.seal_replay(chunk, "s2c3-seal-test", "digits_mlp")
    # an EVIDENCE-labelled record is refused
    record = json.loads((chunk / "job_record.json").read_text())
    record["label"] = "EVIDENCE"
    (chunk / "job_record.json").write_text(json.dumps(record) + "\n")
    lib._write_sums(chunk)
    with pytest.raises(replay.Stop, match="ENGINEERING_ONLY"):
        replay.seal_replay(chunk, "s2c3-seal-test", "digits_mlp")
    # a tampered transferred output is refused
    record["label"] = replay.LABEL
    (chunk / "job_record.json").write_text(json.dumps(record) + "\n")
    (chunk / "out.tar").write_bytes(b"tampered\n")
    with pytest.raises(replay.Stop, match="SHA256SUMS"):
        replay.seal_replay(chunk, "s2c3-seal-test", "digits_mlp")


def test_seal_refuses_traversal_and_a_wrong_record_schema(tmp_path, monkeypatch):
    monkeypatch.setattr(lib, "SEALED_ROOT", tmp_path / "sealed")
    (tmp_path / "sealed").mkdir()
    chunk = _sealable_output(tmp_path)
    record = json.loads((chunk / "job_record.json").read_text())
    record["run_id"] = ".."
    (chunk / "job_record.json").write_text(json.dumps(record) + "\n")
    lib._write_sums(chunk)
    with pytest.raises(replay.Stop, match="invalid sealed path"):
        replay.seal_replay(chunk, "..", "digits_mlp")
    record = json.loads((chunk / "job_record.json").read_text())
    record["schema"] = "other/1"
    (chunk / "job_record.json").write_text(json.dumps(record) + "\n")
    with pytest.raises(replay.Stop, match="replay record"):
        replay.seal_replay(chunk, "s2c3-x", "digits_mlp")


def test_run_replay_writes_a_stop_record_on_prep_failure(tmp_path):
    with pytest.raises(replay.Stop, match="preparation failed"):
        replay.run_replay(tmp_path, SPEC)
    record = json.loads((tmp_path / "job_record.json").read_text())
    assert record["schema"] == replay.RECORD_SCHEMA and record["status"] == "STOP_PREP"
    assert record["label"] == replay.LABEL and record["replay_marker"] == replay.REPLAY_MARKER
    assert "STOP:" in record["stop"]
    assert (tmp_path / "SHA256SUMS").is_file() and (tmp_path / "work.tar").is_file()


def test_run_replay_refuses_a_second_attempt(tmp_path):
    (tmp_path / "job_record.json").write_text('{"schema": "s2_c3_replay_record/v1"}\n')
    with pytest.raises(replay.Stop, match="no retry"):
        replay.run_replay(tmp_path, SPEC)


def test_openml_expected_set_equals_the_tasl_set():
    assert replay.expected_tasl_blockers("openml_credit_approval") == replay.TASL_BLOCKER_GATES
