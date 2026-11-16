"""Tests for the R1-S2C3-DRIVER additions: the reviewed TASL-only shim and the declared-inputs audit.

No GPU, no network, no HTCondor, no /ceph, no llama-server: every test is synthetic.  The patched runtime module
tests build a throw-away copy of ``r1/exam/runtime.py`` with the reviewed shim applied and stub the modules runtime
imports, so the replay-mode predicates under test are the exact bytes the job shadow-executes.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "sweep2"))
import s2_c2_lib as lib  # noqa: E402
import s2_c3_replay as replay  # noqa: E402

SPEC = json.loads((ROOT / "sweep2" / "spec.replay.example.json").read_text())
SPEC_PATHS = [ROOT / "sweep2" / name for name in
              ("spec.replay.example.json", "spec.replay.openml_credit_approval.json",
               "spec.replay.openml_ionosphere.json")]
SHIM = ROOT / replay.SHIM_PATH
DECLARED = ROOT / replay.DECLARED_PATH
INPUTS = ROOT / replay.INPUTS_DIR


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def spec_copy() -> dict:
    return copy.deepcopy(SPEC)


def declared_copy() -> dict:
    return copy.deepcopy(json.loads(DECLARED.read_text()))


def job0() -> dict:
    return json.loads((INPUTS / "digits_mlp__s9011" / "job.json").read_text())


def stage_flat(tmp_path: Path) -> Path:
    """Stage the job sandbox the driver expects: pinned roots + declared manifest + every declared file item."""
    stage = tmp_path / "stage"
    stage.mkdir(parents=True, exist_ok=True)
    shutil_copy(INPUTS / "SHA256SUMS", stage / replay.STAGED_SHA256SUMS)
    for root in replay.ROOTS:
        shutil_copy(INPUTS / root / "job.json", stage / replay.STAGED_JOB.format(root=root))
        shutil_copy(INPUTS / root / "campaign_manifest.json", stage / replay.STAGED_MANIFEST.format(root=root))
    shutil_copy(DECLARED, stage / replay.DECLARED_STAGED)
    declared = json.loads(DECLARED.read_text())
    for item in declared["items"]:
        if item.get("kind") == "file":
            shutil_copy(ROOT / item["path"], stage / item["staged"])
    return stage


def shutil_copy(src: Path, dest: Path) -> None:
    dest.write_bytes(Path(src).read_bytes())


# ------------------------------------------------------------------ declared inputs
def test_declared_inputs_manifest_is_pinned_in_every_replay_spec():
    for path in SPEC_PATHS:
        spec = json.loads(path.read_text())
        assert spec["driver_shim"] == {"path": replay.SHIM_PATH, "sha256": replay.SHIM_SHA256,
                                       "targets": list(replay.SHIM_TARGETS)}
        assert spec["declared_inputs"] == {"path": replay.DECLARED_PATH, "sha256": replay.DECLARED_SHA256,
                                           "staged": replay.DECLARED_STAGED}
        assert replay.validate_spec(spec)["node"] in replay.NODES
    assert sha(SHIM.read_bytes()) == replay.SHIM_SHA256
    assert sha(DECLARED.read_bytes()) == replay.DECLARED_SHA256


def test_declared_inputs_local_audit_verifies_every_file_and_value(tmp_path):
    stage = stage_flat(tmp_path)
    declared = replay.load_declared_inputs(stage, SPEC)
    report = replay.verify_declared_inputs(stage, SPEC, declared, cfg=job0()["authority_config"])
    assert report["failures"] == [] and report["items"] == len(declared["items"])
    kinds = {row["kind"] for row in report["verified"]}
    assert {"file", "value", "staged_tree"} <= kinds
    # all 8 declared files are staged flat (the two patches, criteria and the SHA256SUMS are among them)
    assert len(replay._declared_file_items(declared)) == 8
    # every TASL-only authorization input is bound by the same sha256 the B2 configuration records
    cfg = job0()["authority_config"]
    pins = declared["pins"]
    assert pins["stage_a_table_sha256"] == cfg["stage_a_table_sha256"]
    assert pins["stage_a_amendment_table_sha256"] == cfg["stage_a_amendment_table_sha256"]
    assert pins["stage_a_amendment_acceptance_sha256"] == cfg["stage_a_amendment_acceptance_sha256"]
    assert pins["prompts_sha256"] == cfg["prompts_sha256"]
    assert pins["rule_sha256"] == cfg["rule_sha256"]


def test_declared_inputs_stop_on_tampered_or_missing_file(tmp_path):
    stage = stage_flat(tmp_path)
    declared = replay.load_declared_inputs(stage, SPEC)
    (stage / "S2C3_IN_stage_a_table_t7h8.json").write_text("{}\n")
    with pytest.raises(replay.Stop, match="declared-inputs audit failed"):
        replay.verify_declared_inputs(stage, SPEC, declared, cfg=job0()["authority_config"])
    stop = json.loads((stage / "DECLARED_INPUTS_STOP.json").read_text())
    assert stop["failures"][0]["id"] == "stage_a_table_t7h8"
    stage2 = stage_flat(tmp_path / "two")
    declared2 = replay.load_declared_inputs(stage2, SPEC)
    (stage2 / "S2C3_IN_prompts.jsonl").unlink()
    with pytest.raises(replay.Stop, match="declared-inputs audit failed"):
        replay.verify_declared_inputs(stage2, SPEC, declared2, cfg=job0()["authority_config"])
    assert "stage_a_prompts" not in [row["id"] for row in
                                     json.loads((stage2 / "DECLARED_INPUTS_STOP.json").read_text())["verified"]]


def test_declared_inputs_refuse_manifest_pins_that_differ_from_the_authority_config(tmp_path):
    stage = stage_flat(tmp_path)
    declared = declared_copy()
    declared["pins"]["stage_a_table_sha256"] = "0" * 64
    with pytest.raises(replay.Stop, match="authority_config|declared-inputs audit failed"):
        replay.verify_declared_inputs(stage, SPEC, declared, cfg=job0()["authority_config"])


def test_declared_inputs_refuse_a_manifest_sha_that_differs_from_the_spec(tmp_path):
    stage = stage_flat(tmp_path)
    (stage / replay.DECLARED_STAGED).write_text(json.dumps(declared_copy()) + "\n")
    with pytest.raises(replay.Stop, match="declared-inputs manifest sha256"):
        replay.load_declared_inputs(stage, SPEC)


def test_declared_values_are_checked_not_assumed(tmp_path):
    stage = stage_flat(tmp_path)
    declared = declared_copy()
    for item in declared["items"]:
        if item["id"] == "model_gguf":
            item["value"] = 1
    with pytest.raises(replay.Stop, match="declared value"):
        replay.verify_declared_inputs(stage, SPEC, declared, cfg=job0()["authority_config"])


def test_openml_cache_archive_is_deterministic_and_matches_the_declared_tree(tmp_path):
    declared = json.loads(DECLARED.read_text())
    archive_item = next(item for item in declared["items"] if item["id"] == "openml_cache_archive")
    archive = ROOT / archive_item["path"]
    assert sha(archive.read_bytes()) == archive_item["sha256"]
    dest = tmp_path / "unpacked"
    replay._safe_extract(archive, dest)
    for node in replay.OPENML_NODES:
        root = dest / node / "data_cache"
        entries = [(path.relative_to(root).as_posix(), sha(path.read_bytes()))
                   for path in sorted(root.rglob("*")) if path.is_file()]
        item = next(row for row in declared["items"] if row["id"] == f"{node}_cache")
        assert replay._tree_sha(entries) == item["tree_sha256"]
        assert {row["path"]: row["sha256"] for row in item["files"]} == dict(entries)


def test_safe_extract_refuses_traversal_and_links(tmp_path):
    bad = tmp_path / "bad.tar.gz"
    with tarfile.open(bad, "w:gz") as tar:
        info = tarfile.TarInfo("../escape.txt")
        info.size = 1
        tar.addfile(info, io.BytesIO(b"x"))
    with pytest.raises(replay.Stop, match="escapes the extraction root"):
        replay._safe_extract(bad, tmp_path / "out")
    link = tmp_path / "link.tar.gz"
    with tarfile.open(link, "w:gz") as tar:
        info = tarfile.TarInfo("link")
        info.type = tarfile.SYMTYPE
        info.linkname = "/etc/passwd"
        tar.addfile(info)
    with pytest.raises(replay.Stop, match="not a regular file/dir"):
        replay._safe_extract(link, tmp_path / "out2")


def _fake_harness(tmp_path: Path, ignore: bool) -> Path:
    harness = tmp_path / "harness"
    (harness / "r1").mkdir(parents=True)
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
    subprocess.run(["git", "init", "-q", str(harness)], check=True, env=env)
    (harness / ".gitignore").write_text("experiments/**\n" if ignore else "")
    subprocess.run(["git", "-C", str(harness), "add", ".gitignore"], check=True, env=env)
    subprocess.run(["git", "-C", str(harness), "commit", "-qm", "pinned"], check=True, env=env)
    return harness


def test_stage_openml_cache_installs_at_the_campaign_path_and_requires_gitignore(tmp_path):
    stage = stage_flat(tmp_path)
    declared = replay.load_declared_inputs(stage, SPEC)
    harness = _fake_harness(tmp_path, ignore=False)
    with pytest.raises(replay.Stop, match="not gitignored"):
        replay.stage_openml_cache(stage, declared, harness)
    harness = _fake_harness(tmp_path / "two", ignore=True)
    stage2 = stage_flat(tmp_path / "two_stage")
    declared = replay.load_declared_inputs(stage2, SPEC)
    report = replay.stage_openml_cache(stage2, declared, harness)
    assert report["installed"] == {"openml_credit_approval_cache": "702a0b3cc68d694cc7f3465aee28b0a87afa506026d3ffc2c8916dd4f68b57a8",
                                   "openml_ionosphere_cache": "65dfc44c7200537d2c2c02b71070e6a0436f76450d4274513fd85061fc54dbf7"}
    for node in replay.OPENML_NODES:
        target = harness / replay.OPENML_CACHE_REL / node / "data_cache"
        assert target.is_dir() and (target / "openml").is_dir()
    assert subprocess.check_output(["git", "-C", str(harness), "status", "--porcelain"], text=True) == ""
    report = replay.verify_declared_inputs(stage2, SPEC, declared, installed_cache=report)
    assert report["failures"] == []


def test_stage_openml_cache_refuses_a_tampered_archive(tmp_path):
    stage = stage_flat(tmp_path)
    declared = replay.load_declared_inputs(stage, SPEC)
    archive = stage / "S2C3_IN_openml_cache.tar.gz"
    archive.write_bytes(archive.read_bytes() + b"tamper")
    with pytest.raises(replay.Stop, match="changed after the declared-inputs check"):
        replay.stage_openml_cache(stage, declared, _fake_harness(tmp_path / "h", ignore=True))


# ------------------------------------------------------------------ shim scope
def test_shim_scope_is_additions_only_and_touches_no_numeric_logic():
    scope = replay.check_shim_scope(SHIM.read_text())
    assert scope["files"] == list(replay.SHIM_TARGETS)
    assert scope["removed_lines"] == 0 and scope["additions_only"] is True
    assert scope["touches_no_trial_audit_scoring"] is True
    assert set(scope["hunks"]) == set(replay.SHIM_ALLOWED_ANCHORS)


@pytest.mark.parametrize("mutate, match", [
    (lambda t: t.replace("+    if _s2c3_declared() is not None:\n",
                         "+    if _s2c3_declared() is not None:\n+        run_config(node, {}, [], 'x')\n"), "trial/audit"),
    (lambda t: t.replace("+def _s2c3_host_check(cfg, out):",
                         "+def _s2c3_host_check(cfg, out):\n+    paired([], [])\n"), "trial/audit"),
    (lambda t: t.replace("a/r1/exam/runtime.py", "a/r1/exam/other.py").replace(
        "b/r1/exam/runtime.py", "b/r1/exam/other.py"), "only"),
    (lambda t: t.replace("+    from r1.exam.runtime import _s2c3_declared, _s2c3_require_worker_host\n",
                         "-    import platform\n"), "may only add"),
    (lambda t: t.replace("@@ -301,7 +301,71 @@ def read_registry(path):",
                         "@@ -301,7 +301,71 @@ def whatever(path):"), "allowlist"),
    (lambda t: "", "empty"),
])
def test_shim_scope_refuses_anything_else(mutate, match):
    with pytest.raises(replay.Stop, match=match):
        replay.check_shim_scope(mutate(SHIM.read_text()))


def test_shim_scope_counts_are_the_reviewed_shape():
    text = SHIM.read_text()
    added = [line for line in text.splitlines() if line.startswith("+") and not line.startswith("+++")]
    removed = [line for line in text.splitlines() if line.startswith("-") and not line.startswith("---")]
    assert len(removed) == 0
    assert len(added) == 72
    assert len([line for line in text.splitlines() if line.startswith("@@")]) == 4


# ------------------------------------------------------------------ applying both reviewed patches
def _temp_git_paper(tmp_path: Path) -> tuple[Path, str]:
    paper = tmp_path / "paper"
    for rel in replay.SHIM_TARGETS:
        (paper / rel).parent.mkdir(parents=True, exist_ok=True)
        (paper / rel).write_bytes((ROOT / rel).read_bytes())
    env = {"GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
           "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.invalid"}
    subprocess.run(["git", "init", "-q", str(paper)], check=True, env=env)
    subprocess.run(["git", "-C", str(paper), "add", *replay.SHIM_TARGETS], check=True, env=env)
    subprocess.run(["git", "-C", str(paper), "commit", "-qm", "pinned"], check=True, env=env)
    head = subprocess.check_output(["git", "-C", str(paper), "rev-parse", "HEAD"], text=True).strip()
    return paper, head


def test_reviewed_patches_apply_pin_both_patched_sources_and_keep_the_checkout_clean(tmp_path, monkeypatch):
    paper, head = _temp_git_paper(tmp_path)
    monkeypatch.setattr(replay, "PAPER_COMMIT", head)
    before = {rel: sha((paper / rel).read_bytes()) for rel in replay.SHIM_TARGETS}
    result = replay.apply_reviewed_patches(
        paper, [{"kind": "label", "path": ROOT / replay.PATCH_PATH},
                {"kind": "shim", "path": SHIM}], tmp_path / "work_patch")
    assert result["patched_source_sha256"] == replay.PATCHED_SOURCE_SHA256
    assert sha(Path(result["patched_runtime_source"]).read_bytes()) == replay.PATCHED_SOURCE_SHA256["r1/exam/runtime.py"]
    assert sha(Path(result["patched_campaign_source"]).read_bytes()) == \
        replay.PATCHED_SOURCE_SHA256["r1/exam/campaign.py"]
    assert sha(Path(result["patched_runner_source"]).read_bytes()) == \
        replay.PATCHED_SOURCE_SHA256["r1/scripts/exam_runner.py"]
    assert result["label_scope"]["execution_label_only"] is True
    assert result["shim_scope"]["additions_only"] is True
    assert {rel: sha((paper / rel).read_bytes()) for rel in replay.SHIM_TARGETS} == before
    assert subprocess.check_output(["git", "-C", str(paper), "status", "--porcelain"], text=True) == ""
    # the patched campaign wires require_worker_host to the replay branch before the TASL host pin
    tree = ast.parse(Path(result["patched_campaign_source"]).read_text())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "require_worker_host")
    body = [node for node in function.body if not (isinstance(node, ast.Expr)
                                                   and isinstance(node.value, ast.Constant))]
    assert isinstance(body[0], ast.ImportFrom) and body[0].module == "r1.exam.runtime"
    assert isinstance(body[1], ast.If) and "_s2c3_declared" in ast.dump(body[1].test)


def test_reviewed_patches_refuse_a_tampered_shim(tmp_path, monkeypatch):
    paper, head = _temp_git_paper(tmp_path)
    monkeypatch.setattr(replay, "PAPER_COMMIT", head)
    tampered = tmp_path / "shim.diff"
    tampered.write_text(SHIM.read_text() + "\n")
    with pytest.raises(replay.Stop, match="shim patch sha256"):
        replay.apply_reviewed_patches(paper, [{"kind": "label", "path": ROOT / replay.PATCH_PATH},
                                              {"kind": "shim", "path": tampered}],
                                      tmp_path / "work_patch")


# ------------------------------------------------------------------ the replay-mode shim predicate (patched runtime)
_STUBS = {
    "r1/__init__.py": "",
    "r1/exam/__init__.py": "",
    "r1/exam/analyze.py": ("def load_rule(path, sha):\n    return ({}, sha)\n\n\n"
                           "def is_v2(rule):\n    return False\n\n\n"
                           "def thinking_off_capable(*a, **k):\n    return True\n"),
    "r1/exam/stage_a.py": "def prefill_metadata(ctx):\n    return {}\n",
    "r1/exam/campaign.py": ("def read_rows(path):\n    return []\n\n\ndef write_json(path, data):\n"
                            "    return None\n\n\ndef require_worker_host(job, node=None):\n"
                            "    raise RuntimeError('stub')\n"),
    "r1/exam/guards.py": (
        "import hashlib\nfrom pathlib import Path\n\n\n"
        "def digest_file(path):\n    return hashlib.sha256(Path(path).read_bytes()).hexdigest()\n\n\n"
        "def licence_blockers(*a, **k):\n    return []\n\n\n"
        "def quantization_blockers(*a, **k):\n    return []\n\n\n"
        "def space_check(path):\n    return None\n\n\n"
        "def artifact_label(spec):\n    return 'x'\n\n\n"
        "def paired_instance_bootstrap(a, b):\n    return {}\n"),
    "r1/exam/namespace.py": "def check_exam_seeds(*a, **k):\n    return None\n",
    "r1/exam/cooperative_lease.py": "class LeaseStop(RuntimeError):\n    pass\n",
    "r1/scripts/__init__.py": "",
    "r1/scripts/llama_server_instance.py": "",
    "r1/scripts/c3_label_sweep.py": ("class RunnerWatchdog:\n    pass\n\n\n"
                                     "def stop_tree(*a, **k):\n    return None\n"),
    "yaml.py": "def safe_load(text):\n    return {}\n",
    "r1/c3/__init__.py": "",
    "r1/c3/prior_model.py": "def parse_typed_answer(text):\n    return None\n",
    "r1/exam/cache_io.py": "def read_chunks(*a, **k):\n    return []\n",
    "r1/exam/cache_false.py": "class D3EvidenceStop(RuntimeError):\n    pass\n",
}


def _patched_runtime_tree(tmp_path: Path) -> Path:
    root = tmp_path / "shim_tree"
    for rel, text in _STUBS.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    # only the runtime half of the shim is needed here; the campaign stub above stays a stub
    (root / "r1/exam/runtime.py").write_bytes((ROOT / "r1/exam/runtime.py").read_bytes())
    subprocess.run(["git", "apply", "--include=r1/exam/runtime.py", str(SHIM)], cwd=str(root), check=True,
                   capture_output=True, text=True)
    return root


def _patched_b1_tree(tmp_path: Path) -> Path:
    """A stub-seeded tree carrying the reviewed shim (runtime + campaign + exam_runner) and the real observer."""
    root = _patched_runtime_tree(tmp_path)
    (root / "r1/scripts").mkdir(parents=True, exist_ok=True)
    (root / "r1/scripts/exam_runner.py").write_bytes((ROOT / "r1/scripts/exam_runner.py").read_bytes())
    (root / "r1/exam/observer.py").write_bytes((ROOT / "r1/exam/observer.py").read_bytes())
    acceptance = root / "docs/r1/reports/OPS_O1_20261104.md"
    acceptance.parent.mkdir(parents=True, exist_ok=True)
    acceptance.write_bytes((ROOT / "docs/r1/reports/OPS_O1_20261104.md").read_bytes())
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "apply", "--include=r1/scripts/exam_runner.py", str(SHIM)],
                   check=True, capture_output=True, text=True)
    return root


def _import_patched_b1(tmp_path: Path, monkeypatch):
    root = _patched_b1_tree(tmp_path)
    for name in [name for name in sys.modules if name == "r1" or name.startswith("r1.")]:
        del sys.modules[name]
    monkeypatch.syspath_prepend(str(root))
    import r1.exam.runtime as runtime  # noqa: PLC0415
    import r1.scripts.exam_runner as exam_runner  # noqa: PLC0415
    import r1.exam.observer as observer  # noqa: PLC0415
    return runtime, exam_runner, observer


def _stage_declared_tables(tmp_path: Path) -> tuple[Path, Path, dict]:
    """A declared sandbox with the two sha-pinned Stage A copies + manifest, and the relocated B2 config."""
    declared = declared_copy()
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    (sandbox / replay.DECLARED_STAGED).write_text(json.dumps(declared))
    for item in declared["items"]:
        if item.get("kind") == "file":
            (sandbox / item["staged"]).write_bytes((ROOT / item["path"]).read_bytes())
    cfg = dict(job0()["authority_config"])
    for key, staged in (("stage_a_table", "S2C3_IN_stage_a_table_t7h8.json"),
                        ("stage_a_amendment_table", "S2C3_IN_stage_a_amendment_table_t7j10.json")):
        path = sandbox / staged
        assert sha(path.read_bytes()) == cfg[key + "_sha256"]
        cfg[key] = str(path)
    return sandbox, sandbox / replay.DECLARED_STAGED, cfg


def test_b1_regression_stage_a_pass_set_is_reached_off_tasl_and_relocated(tmp_path, monkeypatch):
    """B1 regression: the real B2 root path (observer._authorized_candidate -> stage_a_pass_set).

    Off TASL and WITHOUT the replay switch the missing TASL tables make the Stage A pass-set read raise (that is
    exactly the STOP the review found would happen after the model fetch); with the replay env + declared sha-bound
    copies it resolves to the registry row.  No server/model is involved in either branch.
    """
    runtime, exam_runner, observer = _import_patched_b1(tmp_path, monkeypatch)
    job = job0()
    registry_candidate = copy.deepcopy(job["candidate"])
    registry_candidate["runtime"]["footprint_mib"] = "TODO_VERIFY_ON_HOST"  # the committed registry value
    registry = {"candidates": [registry_candidate], "software_anchors": [], "sensitivities": []}
    # unshimmed: the TASL-absolute tables do not exist off TASL -> the stage_a_pass_set read refuses
    with pytest.raises(BaseException) as excinfo:
        observer._authorized_candidate(job, job["authority_config"], registry)
    assert isinstance(excinfo.value, (FileNotFoundError, OSError))
    # shimmed: the same call resolves both declared tables after their sha256 checks
    sandbox, manifest_path, cfg = _stage_declared_tables(tmp_path)
    monkeypatch.setenv(replay.REPLAY_DECLARED_ENV, str(manifest_path))
    monkeypatch.setenv(replay.REPLAY_ROOT_ENV, str(sandbox))
    monkeypatch.setenv(replay.REPLAY_SANDBOX_ENV, str(sandbox))
    assert exam_runner.stage_a_pass_set(cfg, {"gemma4_31b"}, v2=True)["gemma4_31b"]["qualification"]
    assert observer._authorized_candidate(job, cfg, registry) is True
    # a tampered declared copy inside stage_a_pass_set is a STOP (same sha256 check as author_gate)
    (sandbox / "S2C3_IN_stage_a_table_t7h8.json").write_text("{}\n")
    with pytest.raises(BaseException) as excinfo:
        exam_runner.stage_a_pass_set(cfg, {"gemma4_31b"}, v2=True)
    assert "sha256 mismatch" in str(excinfo.value)


def test_replay_host_check_keeps_the_dryrun_refusal_and_the_disk_floor(tmp_path, monkeypatch):
    """m1: the replay host branch drops only the TASL pins, not the production DRYRUN-env refusal/disk floor."""
    runtime = _import_patched_runtime(tmp_path, monkeypatch)
    manifest = tmp_path / "declared.json"
    manifest.write_text(json.dumps(declared_copy()))
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    monkeypatch.setenv(replay.REPLAY_DECLARED_ENV, str(manifest))
    monkeypatch.setenv(replay.REPLAY_SANDBOX_ENV, str(sandbox))
    monkeypatch.setattr(runtime.platform, "node", lambda: "g3605.nemo.privat")
    calls = []
    monkeypatch.setattr(runtime, "space_check", lambda path: calls.append(Path(path)))
    runtime._s2c3_host_check({}, sandbox / "out")
    assert calls == [sandbox]
    for key in ("R1_DRYRUN", "R1_FAKE_OLLAMA_ROOT", "R1_EXAM_DRYRUN"):
        monkeypatch.setenv(key, "1")
        with pytest.raises(RuntimeError, match="DRYRUN environment must not enter a production exam"):
            runtime._s2c3_host_check({}, sandbox / "out")
        monkeypatch.delenv(key)
    def low_space(path):
        raise RuntimeError("STOP: available space 1 below 100 GB")
    monkeypatch.setattr(runtime, "space_check", low_space)
    with pytest.raises(RuntimeError, match="below 100 GB"):
        runtime._s2c3_host_check({}, sandbox / "out")


def _import_patched_runtime(tmp_path: Path, monkeypatch):
    root = _patched_runtime_tree(tmp_path)
    for name in [name for name in sys.modules if name == "r1" or name.startswith("r1.")]:
        del sys.modules[name]
    monkeypatch.syspath_prepend(str(root))
    import r1.exam.runtime as runtime  # noqa: PLC0415 - deliberately imported from the throw-away tree
    return runtime


def test_shim_is_inert_without_the_replay_environment(tmp_path, monkeypatch):
    runtime = _import_patched_runtime(tmp_path, monkeypatch)
    assert runtime._s2c3_declared() is None
    original = Path("/some/tasl/path/table.json")
    assert runtime._s2c3_relocate({"stage_a_table_sha256": "0" * 64}, "stage_a_table", original) == original
    # without the replay env the normal TASL host gate is unchanged
    monkeypatch.setattr(runtime.platform, "node", lambda: "g3605.nemo.privat")
    with pytest.raises(RuntimeError, match="approved portal host"):
        runtime.host_check({"host": "TASL-7", "work_dir": "/home/dowling/exam-x/work",
                            "models_dir": "/home/dowling/exam-x/models"}, tmp_path / "out")


def test_shim_host_check_refuses_tasl_and_enforces_the_declared_sandbox(tmp_path, monkeypatch):
    runtime = _import_patched_runtime(tmp_path, monkeypatch)
    manifest = tmp_path / "declared.json"
    manifest.write_text(json.dumps(declared_copy()))
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    monkeypatch.setenv(replay.REPLAY_DECLARED_ENV, str(manifest))
    monkeypatch.setenv(replay.REPLAY_ROOT_ENV, str(tmp_path))
    monkeypatch.setenv(replay.REPLAY_SANDBOX_ENV, str(sandbox))
    assert runtime._s2c3_declared()["label"] == replay.LABEL
    cfg = {"host": "TASL-7"}
    monkeypatch.setattr(runtime.platform, "node", lambda: "TASL-7")
    with pytest.raises(RuntimeError, match="must not run on an approved exam host"):
        runtime._s2c3_host_check(cfg, sandbox / "out")
    monkeypatch.setattr(runtime.platform, "node", lambda: "g3605.nemo.privat")
    assert runtime._s2c3_host_check(cfg, sandbox / "out") is None
    with pytest.raises(RuntimeError, match="escapes the declared sandbox root"):
        runtime._s2c3_host_check(cfg, tmp_path / "elsewhere")
    monkeypatch.delenv(replay.REPLAY_SANDBOX_ENV)
    with pytest.raises(RuntimeError, match="sandbox root is not declared"):
        runtime._s2c3_host_check(cfg, sandbox / "out")
    # a manifest that is not the ENGINEERING_ONLY replay manifest is refused
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(dict(declared_copy(), label="EVIDENCE")))
    monkeypatch.setenv(replay.REPLAY_SANDBOX_ENV, str(sandbox))
    monkeypatch.setenv(replay.REPLAY_DECLARED_ENV, str(bad))
    with pytest.raises(RuntimeError, match="declared-inputs manifest is invalid"):
        runtime._s2c3_declared()


def test_shim_relocates_the_stage_a_tables_by_sha256(tmp_path, monkeypatch):
    runtime = _import_patched_runtime(tmp_path, monkeypatch)
    declared = declared_copy()
    manifest = tmp_path / "declared.json"
    manifest.write_text(json.dumps(declared))
    stage = tmp_path / "sandbox"
    stage.mkdir()
    for item in declared["items"]:
        if item.get("kind") == "file":
            (stage / item["staged"]).write_bytes((ROOT / item["path"]).read_bytes())
    monkeypatch.setenv(replay.REPLAY_DECLARED_ENV, str(manifest))
    monkeypatch.setenv(replay.REPLAY_ROOT_ENV, str(stage))
    cfg = job0()["authority_config"]
    relocated = runtime._s2c3_relocate(cfg, "stage_a_table", Path(cfg["stage_a_table"]))
    assert relocated == stage / "S2C3_IN_stage_a_table_t7h8.json"
    assert sha(relocated.read_bytes()) == cfg["stage_a_table_sha256"]
    assert runtime._s2c3_relocate(cfg, "stage_a_amendment_table",
                                  Path(cfg["stage_a_amendment_table"])) == \
        stage / "S2C3_IN_stage_a_amendment_table_t7j10.json"
    # a non-declared key keeps the committed relative path
    assert runtime._s2c3_relocate(cfg, "rule", Path(cfg["rule"])) == Path(cfg["rule"])
    # a tampered declared copy is a STOP, not a silent fallback to the TASL path
    (stage / "S2C3_IN_stage_a_table_t7h8.json").write_text("{}\n")
    with pytest.raises(RuntimeError, match="declared input stage_a_table sha256 mismatch"):
        runtime._s2c3_relocate(cfg, "stage_a_table", Path(cfg["stage_a_table"]))


def test_shim_worker_host_helper_returns_the_real_node_off_tasl(tmp_path, monkeypatch):
    runtime = _import_patched_runtime(tmp_path, monkeypatch)
    manifest = tmp_path / "declared.json"
    manifest.write_text(json.dumps(declared_copy()))
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    monkeypatch.setenv(replay.REPLAY_DECLARED_ENV, str(manifest))
    monkeypatch.setenv(replay.REPLAY_SANDBOX_ENV, str(sandbox))
    monkeypatch.setattr(runtime.platform, "node", lambda: "g3605.nemo.privat")
    assert runtime._s2c3_require_worker_host({"out": str(sandbox / "out")}) == "g3605"
    monkeypatch.setattr(runtime.platform, "node", lambda: "TASL-7")
    with pytest.raises(RuntimeError, match="approved exam host"):
        runtime._s2c3_require_worker_host({"out": str(sandbox / "out")})


# ------------------------------------------------------------------ replay env plumbing
def test_replay_env_is_the_only_shim_switch(tmp_path):
    env = replay.replay_env(tmp_path)
    assert set(env) == {replay.REPLAY_DECLARED_ENV, replay.REPLAY_ROOT_ENV, replay.REPLAY_SANDBOX_ENV}
    assert env[replay.REPLAY_DECLARED_ENV].endswith(replay.DECLARED_STAGED)
    campaign = replay.campaign_env(tmp_path / "paper", tmp_path / "harness", "http://127.0.0.1:18130/v1",
                                   cwd=tmp_path)
    assert campaign[replay.REPLAY_SANDBOX_ENV] == str(tmp_path.resolve())
    plain = replay.campaign_env(tmp_path / "paper", tmp_path / "harness", "http://127.0.0.1:18130/v1")
    assert not any(key in plain for key in (replay.REPLAY_DECLARED_ENV, replay.REPLAY_ROOT_ENV,
                                            replay.REPLAY_SANDBOX_ENV))


def test_spec_refuses_mutated_shim_or_declared_blocks():
    for mutate in (lambda s: s["driver_shim"].__setitem__("sha256", "0" * 64),
                   lambda s: s["driver_shim"].__setitem__("targets", ["r1/exam/campaign.py"]),
                   lambda s: s["driver_shim"].__setitem__("extra", 1),
                   lambda s: s["declared_inputs"].__setitem__("sha256", "0" * 64),
                   lambda s: s["declared_inputs"].__setitem__("staged", "OTHER.json"),
                   lambda s: s["declared_inputs"].__setitem__("extra", 1)):
        spec = spec_copy()
        mutate(spec)
        with pytest.raises(replay.Stop):
            replay.validate_spec(spec)


# ------------------------------------------------------------------ operator audit + seal bindings
def test_audit_declared_inputs_verifies_the_committed_plan_and_ships_the_tasl_only_items():
    report = replay.audit_declared_inputs(ROOT, ROOT / "sweep2" / "spec.replay.example.json")
    assert report["failures"] == []
    assert report["binding"]["recomputed"] == replay.BINDING
    assert set(report["tasl_only_items_shipped"]) == {"stage_a_table_t7h8", "stage_a_amendment_table_t7j10",
                                                      "stage_a_prompts", "openml_cache_archive"}
    deferred = {row["id"] for row in report["deferred_to_job_start"]}
    assert {"node_digits_mlp", "node_openml_credit_approval", "node_openml_ionosphere",
            "openml_credit_approval_cache", "openml_ionosphere_cache"} <= deferred


def test_preflight_cli_refuses_before_any_clone_when_the_spec_is_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(replay.Stop):
        replay.main(["preflight", "missing.json"])


def test_seal_refuses_a_record_without_the_shim_and_declared_bindings(tmp_path, monkeypatch):
    monkeypatch.setattr(lib, "SEALED_ROOT", tmp_path / "sealed")
    (tmp_path / "sealed").mkdir()
    chunk = tmp_path / "job"
    chunk.mkdir()
    record = {"schema": replay.RECORD_SCHEMA, "kind": replay.KIND, "run_id": "r", "chunk_id": "digits_mlp",
              "node": "digits_mlp", "label": replay.LABEL, "replay_marker": replay.REPLAY_MARKER,
              "image_digest": replay.IMAGE_DIGEST, "model_sha256": replay.GGUF_SHA256,
              "paper_commit": replay.PAPER_COMMIT, "harness_commit": replay.HARNESS_COMMIT,
              "label_patch": {"patch_sha256": replay.PATCH_SHA256},
              "host": {"fqdn": "g3605.nemo.privat"}}
    (chunk / "job_record.json").write_text(json.dumps(record))
    with pytest.raises(replay.Stop, match="replay driver shim"):
        replay.seal_replay(chunk, "r", "digits_mlp")
    record["driver_shim"] = {"patch_sha256": replay.SHIM_SHA256}
    (chunk / "job_record.json").write_text(json.dumps(record))
    with pytest.raises(replay.Stop, match="patched-source pins"):
        replay.seal_replay(chunk, "r", "digits_mlp")
    record["driver_shim"]["patched_source_sha256"] = replay.PATCHED_SOURCE_SHA256
    (chunk / "job_record.json").write_text(json.dumps(record))
    with pytest.raises(replay.Stop, match="declared-inputs manifest"):
        replay.seal_replay(chunk, "r", "digits_mlp")
    record["declared_inputs"] = {"manifest_sha256": replay.DECLARED_SHA256, "items_declared": 25,
                                 "items_verified": 24}
    (chunk / "job_record.json").write_text(json.dumps(record))
    with pytest.raises(replay.Stop, match="did not verify every item"):
        replay.seal_replay(chunk, "r", "digits_mlp")
