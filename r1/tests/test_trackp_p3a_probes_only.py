"""CPU-only tests for the P.3a attempt-2 probes-only runner (Unit A plan §1c.2).

No GPU, no model, no host: the TASL-7 preflight internals, marker helper and child units are stubbed, and the
attempt-1 root is a synthetic temp tree. The tests pin the fail-closed argument contract, the budget projection
arithmetic, the attempt-1 provenance/hash walk and boot-id gate, the exact reviewed paper HEAD, the M13 template
block, the unit-start re-verification, and the exact two-command DRYRUN/EVIDENCE sequence.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from r1.scripts import trackp_p3a_guarded as G

KEV_COMMIT = "2074cc44256200bb37540103fa4572901faa10f3"
A1_BASES = {"kev-0.8b": "kev", "qwen3.5-4b-base": "qwen_control"}
ROOT_NAME = G.NEW_ROOT_PREFIX + "20261116T120000Z"


def _write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


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
                       boot_id: str = G.EXPECTED_ATTEMPT1_BOOT_ID,
                       stop_events: int = 1, include_boot_id: bool = True) -> Path:
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
    campaign = {"event": "campaign_start", "utc": "2026-10-27T13:02:39Z",
                "pins": {"paper": {"commit": paper_commit, "branch": "trackp-20261026", "dirty": False}}}
    if include_boot_id:
        campaign["boot_id"] = boot_id
    journal = [campaign]
    journal += [{"event": "STOP", "utc": "2026-10-29T01:25:17Z", "gpu_seconds_total": gpu_seconds,
                 "error": "unit failed"} for _ in range(stop_events)]
    (root / "journal.jsonl").write_text("\n".join(json.dumps(event) for event in journal) + "\n")
    (tmp_path / "gpu_lease_log.jsonl").write_text(
        json.dumps({"event": "start", "pid": 11, "monotonic_s": 100.0}) + "\n" +
        json.dumps({"event": "end", "pid": 11, "monotonic_s": 130.0}) + "\n")
    return root


def _runs(tmp_path: Path) -> Path:
    return tmp_path / "runs"


def _set_runs(monkeypatch, tmp_path: Path) -> Path:
    runs = _runs(tmp_path)
    monkeypatch.setenv("R1_RUNS", str(runs))
    return runs


def _ns(tmp_path, **over):
    values = {"root": _runs(tmp_path) / ROOT_NAME, "probes_only": True,
              "base": G.PROBES_ONLY_BASE, "attempt1_root": _runs(tmp_path) / G.ATTEMPT1_ROOT_NAME,
              "a3_short": True, "authorization_amend_sha256": G.AUTHORIZATION_AMEND_SHA256}
    values.update(over)
    return SimpleNamespace(**values)


# ------------------------------------------------------------------ parser / flags

def test_parse_args_accepts_the_probes_only_contract(tmp_path):
    attempt1 = tmp_path / G.ATTEMPT1_ROOT_NAME
    args = G.parse_args(["--root", str(_runs(tmp_path) / ROOT_NAME), "--probes-only",
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


def test_validate_probes_only_refuses_existing_misnamed_or_out_of_runs_roots(tmp_path, monkeypatch):
    runs = _set_runs(monkeypatch, tmp_path)
    runs.mkdir(parents=True)
    args = _ns(tmp_path)
    args.root.mkdir(parents=True)
    with pytest.raises(G.R.TrackPStop, match="already exists"):
        G.validate_probes_only_args(args)
    args.root.rmdir()
    dangling = _ns(tmp_path, root=runs / ROOT_NAME)
    dangling.root.symlink_to(tmp_path / "missing")
    with pytest.raises(G.R.TrackPStop, match="dangling"):
        G.validate_probes_only_args(dangling)
    args = _ns(tmp_path, root=runs / "not-an-attempt2-root")
    with pytest.raises(G.R.TrackPStop, match=G.NEW_ROOT_PREFIX):
        G.validate_probes_only_args(args)
    for bad_stamp in ("20261116T1200Z", "20261316T120000Z", "20261116T120000", "notatime"):
        args = _ns(tmp_path, root=runs / (G.NEW_ROOT_PREFIX + bad_stamp))
        with pytest.raises(G.R.TrackPStop, match="UTC|canonical"):
            G.validate_probes_only_args(args)
    args = _ns(tmp_path, root=tmp_path / "elsewhere" / ROOT_NAME)
    with pytest.raises(G.R.TrackPStop, match="runs directory"):
        G.validate_probes_only_args(args)


def test_validate_probes_only_refuses_relative_attempt1_root_and_attempt1_reuse(tmp_path, monkeypatch):
    _set_runs(monkeypatch, tmp_path)
    args = _ns(tmp_path, attempt1_root=Path("relative") / G.ATTEMPT1_ROOT_NAME)
    with pytest.raises(G.R.TrackPStop, match="attempt1-root must be absolute"):
        G.validate_probes_only_args(args)
    args = _ns(tmp_path)
    args.attempt1_root = args.root / G.ATTEMPT1_ROOT_NAME          # would be nested inside the new root
    with pytest.raises(G.R.TrackPStop, match="may not be reused"):
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


# ------------------------------------------------------------------ MAJOR-1: boot id gate

def test_verify_attempt1_boot_id_gate():
    assert G.verify_attempt1_boot_id(G.EXPECTED_ATTEMPT1_BOOT_ID)["match"] is True
    assert G.verify_attempt1_boot_id(G.EXPECTED_ATTEMPT1_BOOT_ID, G.EXPECTED_ATTEMPT1_BOOT_ID) == {
        "boot_id": G.EXPECTED_ATTEMPT1_BOOT_ID, "attempt1_boot_id": G.EXPECTED_ATTEMPT1_BOOT_ID, "match": True}
    with pytest.raises(G.R.TrackPStop, match="unplanned reboot"):
        G.verify_attempt1_boot_id("00000000-0000-0000-0000-000000000000")
    with pytest.raises(G.R.TrackPStop, match="empty"):
        G.verify_attempt1_boot_id("")


def test_attempt1_provenance_records_and_pins_the_boot_id(tmp_path, monkeypatch):
    root = make_attempt1_root(tmp_path)
    provenance = G.build_attempt1_provenance(root)
    assert provenance["attempt1_boot_id"] == G.EXPECTED_ATTEMPT1_BOOT_ID
    assert provenance["expected_attempt1_boot_id"] == G.EXPECTED_ATTEMPT1_BOOT_ID
    assert "derived_template_id" not in provenance                 # M2: per-unit, not campaign scalar
    assert set(provenance["derived_template_ids_by_family"]) == {"kev", "qwen_control"}
    # a journal that records a different boot id is refused against the reviewed constant
    wrong = make_attempt1_root(tmp_path / "wrong", boot_id="11111111-1111-1111-1111-111111111111")
    changed = G.build_attempt1_provenance(wrong)
    monkeypatch.setattr(G, "EXPECTED_ATTEMPT1_JOURNAL_SHA256", changed["journal_sha256"])
    monkeypatch.setattr(G, "EXPECTED_ATTEMPT1_LEASE_LOG_SHA256", changed["lease_log_sha256"])
    with pytest.raises(G.R.TrackPStop, match="attempt1_boot_id"):
        G.assert_attempt1_pins(changed)
    # a journal with no campaign_start.boot_id cannot be bound to the reviewed run at all
    missing = make_attempt1_root(tmp_path / "missing", include_boot_id=False)
    with pytest.raises(G.R.TrackPStop, match="no boot_id"):
        G.build_attempt1_provenance(missing)


# ------------------------------------------------------------------ MAJOR-2: exact paper HEAD

def _git(repo: Path, *args, check=True) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=check, capture_output=True, text=True).stdout.strip()


def _paper_git_repo(tmp_path: Path) -> tuple[Path, dict]:
    """Throwaway repo mirroring the reviewed layout, with one commit per identity the preflight must judge.

    base -> reviewed code commit C (runner + a test edit)
    C -> docs-only child of C (r1/ unchanged)         -> accepted as ``docs_child_r1_identical``
    C -> genuine mechanical delivery-pin child D      -> accepted as ``delivery_pin_child``
    C -> crafted one-line child with injected code    -> refused
    C -> pin-shaped child that also edits r1/ code    -> refused
    D -> unrelated descendant                         -> refused
    """
    repo = tmp_path / "paper"
    (repo / "r1" / "scripts").mkdir(parents=True)
    (repo / "r1" / "tests").mkdir(parents=True)
    runner = repo / G.PAPER_RUNNER_PATH
    child = repo / G.PAPER_CHILD_SCRIPT
    record = repo / G.CODE_UNITS_RECORD
    record.parent.mkdir(parents=True, exist_ok=True)
    base_runner = G.canonical_paper_head_line("0" * 40) + "\n# reviewed probes-only runner\n"
    runner.write_text(base_runner)
    child.write_text("# child probes script\n")

    def git(*args, check=True):
        return subprocess.run(["git", "-C", str(repo), *args], check=check, capture_output=True,
                              text=True).stdout.strip()

    def commit(base: str, changes: dict, message: str, branch: str) -> str:
        git("checkout", "-q", "-B", branch, base)
        for relative, content in changes.items():
            target = repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        git("add", "-A")
        git("commit", "-qm", message)
        return git("rev-parse", "HEAD")

    git("init", "-q")
    git("config", "user.name", "test")
    git("config", "user.email", "test@example.invalid")
    git("add", "-A")
    git("commit", "-qm", "base")
    commits = {"base": git("rev-parse", "HEAD")}
    code_runner = base_runner + "# round-2 review fixes\n"
    commits["code"] = commit(commits["base"],
                             {G.PAPER_RUNNER_PATH: code_runner,
                              "r1/tests/test_trackp_p3a_probes_only.py": "# reviewed tests\n"},
                             "reviewed code commit", "code")
    commits["docs"] = commit(commits["code"], {G.CODE_UNITS_RECORD: "# code units record\n"},
                             "docs-only child of the reviewed code commit", "docs-child")
    pin_runner = code_runner.replace(G.canonical_paper_head_line("0" * 40),
                                     G.canonical_paper_head_line(commits["code"]))
    commits["pin"] = commit(commits["code"],
                            {G.PAPER_RUNNER_PATH: pin_runner,
                             G.CODE_UNITS_RECORD: f"# code units record\ncode commit {commits['code']}\n"},
                            "delivery pin", "delivery-pin")
    crafted_runner = code_runner.replace(
        G.canonical_paper_head_line("0" * 40),
        G.canonical_paper_head_line(commits["code"]) + '; __import__("os").system("touch /tmp/p3a_pwned")\n')
    commits["crafted"] = commit(commits["code"], {G.PAPER_RUNNER_PATH: crafted_runner},
                                "crafted one-line child", "crafted")
    commits["code_extra"] = commit(commits["code"],
                                   {G.PAPER_RUNNER_PATH: pin_runner,
                                    "r1/tests/test_trackp_p3a_probes_only.py": "# edited in the pin child\n"},
                                   "pin plus an unrelated r1/ edit", "code-extra")
    commits["other"] = commit(commits["pin"], {G.PAPER_RUNNER_PATH: pin_runner + "# after delivery\n"},
                              "unreviewed descendant", "other")
    return repo, commits


def _paper(commit: str, branch: str = G.EXPECTED_PAPER_BRANCH, dirty: bool = False) -> dict:
    return {"commit": commit, "branch": branch, "dirty": dirty, "dirty_files": ["x"] if dirty else []}


def test_verify_paper_head_accepts_only_the_three_reviewed_identities(tmp_path, monkeypatch):
    repo, commits = _paper_git_repo(tmp_path)
    monkeypatch.setattr(G, "EXPECTED_PAPER_HEAD", commits["code"])
    # (i) the reviewed code commit itself, on the branch or detached
    exact = G.verify_paper_head(_paper(commits["code"]), repo=repo)
    assert exact["kind"] == "exact_reviewed_runner_commit" and exact["expected_commit"] == commits["code"]
    assert G.verify_paper_head(_paper(commits["code"], "HEAD"), repo=repo)["kind"] == "exact_reviewed_runner_commit"
    # (ii) a docs-only child of C with a byte-identical r1/ tree
    docs = G.verify_paper_head(_paper(commits["docs"]), repo=repo)
    assert docs["kind"] == "docs_child_r1_identical" and docs["expected_commit"] == commits["code"]
    # (iii) the byte-exact mechanical delivery-pin child D
    pin = G.verify_paper_head(_paper(commits["pin"]), repo=repo)
    assert pin["kind"] == "delivery_pin_child" and pin["expected_commit"] == commits["code"]
    # the expected pin runner blob is exactly C's blob with the one canonical assignment substituted
    expected = G.expected_pin_runner_blob(repo=repo)
    pinned = subprocess.run(["git", "-C", str(repo), "show", f"{commits['pin']}:{G.PAPER_RUNNER_PATH}"],
                            capture_output=True).stdout
    assert pinned == expected
    assert G.canonical_paper_head_line(commits["code"]).encode() in expected
    # a crafted one-line child with injected code has the same diff shape but is REFUSED (round-2 MAJOR-1)
    assert G._delivery_pin_child(commits["crafted"], repo=repo) is False
    with pytest.raises(G.R.TrackPStop, match="not the reviewed code commit"):
        G.verify_paper_head(_paper(commits["crafted"]), repo=repo)
    # a pin-shaped child that also edits another r1/ file is refused
    assert G._delivery_pin_child(commits["code_extra"], repo=repo) is False
    with pytest.raises(G.R.TrackPStop, match="not the reviewed code commit"):
        G.verify_paper_head(_paper(commits["code_extra"]), repo=repo)
    # arbitrary descendants and ancestors are refused
    for commit in (commits["other"], commits["base"]):
        with pytest.raises(G.R.TrackPStop, match="not the reviewed code commit"):
            G.verify_paper_head(_paper(commit), repo=repo)
    with pytest.raises(G.R.TrackPStop, match="paper branch"):
        G.verify_paper_head(_paper(commits["pin"], "trackp-20261026"), repo=repo)


# ------------------------------------------------------------------ MAJOR-1: executing bytes pinned to HEAD

def _executing_git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "executing"
    for relative in G.EXECUTING_FILES:
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"# tracked {relative}\n")
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "test")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "tracked executing files")
    return repo


def test_verify_executing_files_pins_the_executing_bytes_to_head(tmp_path, monkeypatch):
    repo = _executing_git_repo(tmp_path)
    monkeypatch.setattr(G, "EXECUTING_RUNNER", repo / G.PAPER_RUNNER_PATH)
    monkeypatch.setattr(G, "EXPECTED_PAPER_HEAD", _git(repo, "rev-parse", "HEAD"))
    record = G.verify_executing_files(repo=repo)
    assert set(record["files"]) == set(G.EXECUTING_FILES)
    assert record["runner_script_sha256"] == record["files"][G.PAPER_RUNNER_PATH]["sha256"] == _sha(
        repo / G.PAPER_RUNNER_PATH)
    # a normal dirty edit is caught by the byte comparison (R.git_commit would also report it)
    (repo / G.PAPER_CHILD_SCRIPT).write_text("# tampered child\n")
    with pytest.raises(G.R.TrackPStop, match="differs from HEAD"):
        G.verify_executing_files(repo=repo)
    _git(repo, "checkout", "--", ".")
    # an assume-unchanged edit is invisible to `git status --porcelain` but caught by the byte comparison
    _git(repo, "update-index", "--assume-unchanged", G.PAPER_CHILD_SCRIPT)
    (repo / G.PAPER_CHILD_SCRIPT).write_text("# ignored tamper\n")
    assert _git(repo, "status", "--porcelain") == ""
    with pytest.raises(G.R.TrackPStop, match="differs from HEAD"):
        G.verify_executing_files(repo=repo)
    # the executing script outside the tracked checkout (e.g. a modified copy run from /tmp) is refused
    foreign = tmp_path / "foreign_runner.py"
    foreign.write_text("# copy of the runner\n")
    monkeypatch.setattr(G, "EXECUTING_RUNNER", foreign)
    with pytest.raises(G.R.TrackPStop, match="not the tracked runner"):
        G.verify_executing_files(repo=repo)
    # a missing executing file is a STOP, not a skip
    _git(repo, "update-index", "--no-assume-unchanged", G.PAPER_CHILD_SCRIPT)
    _git(repo, "checkout", "--", ".")
    (repo / "r1/c3/train/serialize.py").unlink()
    monkeypatch.setattr(G, "EXECUTING_RUNNER", repo / G.PAPER_RUNNER_PATH)
    with pytest.raises(G.R.TrackPStop, match="missing from the checkout"):
        G.verify_executing_files(repo=repo)


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
    assert provenance["derived_template_ids_by_family"] == G.EXPECTED_DERIVED_TEMPLATE_IDS
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


# ------------------------------------------------------------------ M1: golden rendered token stream

class _StubTokenizer:
    """Deterministic word/line tokenizer for the token-stream-order test (no model, no pool tokenizer)."""

    def encode(self, text, add_special_tokens=False):  # noqa: ARG002
        return [token for token in text.replace("\n", " \n ").split() if token]


def test_golden_field_order_from_the_pinned_renderers():
    """M13 §3.2 golden vector: the declared frame/field_order must match the pinned renderers' actual output.

    The Qwen renderer is exercised from the pinned source with a deterministic stub tokenizer (``prefix`` +
    ``segments``: state, proposal, question, bins, then the Belief/Action readout positions). Kev's special-token
    stream lives in the installed ``kev.model`` package, which is absent locally, so only its record layout
    (state -> proposal+question -> options) is checked here; the token-id check is the skipped test below.
    """
    from r1.c3.train import model as M
    from r1.c3.train.types import BIN_OPTIONS, DecisionPrompt

    prompt = DecisionPrompt(state="STATE-MARKER", proposal="PROPOSAL-MARKER")
    stub = object.__new__(M.BinTokenWrapper)
    stub.list_bins, stub.bin_order, stub.tok = True, list(range(12)), _StubTokenizer()
    text = M.BinTokenWrapper.prefix(stub, prompt)
    markers = ["STATE-MARKER", "Proposed edit:", "PROPOSAL-MARKER", "Question:", "Bins:"]
    positions = [text.index(marker) for marker in markers]
    assert positions == sorted(positions) and len(set(positions)) == len(positions)
    bin_positions = [text.index(f"<b{index}>") for index in range(12)]
    assert bin_positions == sorted(bin_positions)
    assert text.index("<b0>") > text.index("Bins:") and text.index("<b11>") > text.index("<b10>")
    for index, expected in enumerate(BIN_OPTIONS):
        assert f"<b{index}> {expected}" in text
    ids, belief_pos, action_pos, _ = M.BinTokenWrapper.segments(stub, prompt)
    assert ids[belief_pos] == "Belief:" and ids[action_pos] == "Action:"
    assert belief_pos < action_pos and action_pos == len(ids) - 1
    qwen_declared = G.FRAMES["qwen_control"]["field_order"]
    qwen_observed = ["state", "proposal", "question", "bins", "belief", "action"]
    assert qwen_declared == qwen_observed
    # Kev: the pinned wrapper builds state first, then the proposal+question instruction, then the 12 options.
    records, where = M.PointerWrapper.records(SimpleNamespace(), [prompt])
    assert records[0]["state"] == prompt.state and len(where) == 1
    question = records[0]["questions"][0]
    assert question["instr"] == f"{prompt.proposal}\n\n{prompt.question}" and question["options"] == list(BIN_OPTIONS)
    kev_declared = G.FRAMES["kev"]["field_order"]
    assert kev_declared[:2] == ["state", "proposal"] and kev_declared[3] == "options"
    assert G.FRAMES["kev"]["readout"]["decide_token"] == "<|fim_suffix|>"
    assert G.FRAMES["qwen_control"]["readout"]["belief_position"] == "last token of 'Belief:'"
    assert G.FRAMES["qwen_control"]["readout"]["action_position"] == "last token of '\\nAction:'"


def test_golden_token_ids_qwen_from_the_pool_tokenizer():
    """M13 §3.2 token-id golden test; skipped with an explicit reason when the pool tokenizers are absent."""
    try:
        from r1.c3.train import serialize as S
        tokenizers = S.pool_tokenizers()
    except Exception as exc:                                      # transformers/tokenizers/cache absent
        pytest.skip(f"pool tokenizers absent locally ({type(exc).__name__}: {exc}); the token-id golden vector "
                    f"is recorded as a limitation of this CPU-only unit")
    tokenizer = tokenizers[G.PROBES_ONLY_BASE]
    from r1.c3.train import model as M
    from r1.c3.train.types import DecisionPrompt
    prompt = DecisionPrompt(state="STATE-MARKER", proposal="PROPOSAL-MARKER")
    M.add_reserved_tokens(tokenizer)
    stub = object.__new__(M.BinTokenWrapper)
    stub.list_bins, stub.bin_order, stub.tok = True, list(range(12)), tokenizer
    text = M.BinTokenWrapper.prefix(stub, prompt)
    ids = tokenizer.encode(text, add_special_tokens=False)
    bin_ids = [tokenizer.convert_tokens_to_ids(f"<b{index}>") for index in range(12)]
    assert [ids.index(token) for token in bin_ids] == sorted(ids.index(token) for token in bin_ids)
    first_bin = min(ids.index(token) for token in bin_ids)
    state_ids = tokenizer.encode(prompt.state, add_special_tokens=False)
    proposal_ids = tokenizer.encode(prompt.proposal, add_special_tokens=False)
    assert _first_subsequence(ids, state_ids) < _first_subsequence(ids, proposal_ids) < first_bin
    belief_ids = tokenizer.encode("Belief:", add_special_tokens=False)
    action_ids = tokenizer.encode("\nAction:", add_special_tokens=False)
    belief_at = _first_subsequence(ids, belief_ids) + len(belief_ids) - 1
    action_at = _first_subsequence(ids, action_ids) + len(action_ids) - 1
    assert belief_at < action_at


def test_golden_token_ids_kev_from_the_pinned_encoder():
    """M13 §3.2 Kev token-id golden test; skipped with an explicit reason when Kev is absent."""
    pytest.importorskip("kev", reason="installed Kev encoder absent locally; the Kev token-id golden vector is "
                                      "recorded as a limitation of this CPU-only unit")
    from kev import model as km
    from r1.c3.train import model as M
    from r1.c3.train.types import BIN_OPTIONS, DecisionPrompt
    prompt = DecisionPrompt(state="STATE-MARKER", proposal="PROPOSAL-MARKER")
    records, _ = M.PointerWrapper.records(SimpleNamespace(), [prompt])
    tokenizer = km.load_tokenizer(G.DRYRUN_BASE, revision=None)
    encoded = km.encode(tokenizer, records[0], max_state=1024, max_branch=1024, strict=True)
    assert encoded["ids"][-1] == tokenizer.convert_tokens_to_ids("<|fim_suffix|>")
    assert encoded["decide_idx"] == len(encoded["ids"]) - 1
    assert [encoded["ids"][index] for index in encoded["opt_idx"]] == [
        tokenizer.convert_tokens_to_ids(f"<box_end>") for _ in BIN_OPTIONS]


def _first_subsequence(haystack, needle) -> int:
    for start in range(len(haystack) - len(needle) + 1):
        if haystack[start:start + len(needle)] == list(needle):
            return start
    raise AssertionError(f"subsequence {needle!r} not found")


def test_write_json_atomic_uses_replace(tmp_path, monkeypatch):
    replaced = []
    real_replace = G.os.replace

    def fake_replace(source, destination):
        replaced.append((Path(source), Path(destination)))
        return real_replace(source, destination)

    monkeypatch.setattr(G.os, "replace", fake_replace)
    path = tmp_path / "runner_manifest.json"
    G.write_json_atomic(path, {"schema": G.UNIT_MANIFEST_SCHEMA, "a": 1})
    assert json.loads(path.read_text()) == {"schema": G.UNIT_MANIFEST_SCHEMA, "a": 1}
    assert replaced and replaced[0][1] == path and replaced[0][0].name.startswith(".runner_manifest.json.")
    assert not list(tmp_path.glob("*.tmp"))


def test_sidecar_builder_writes_every_m13_field_and_per_unit_provenance_id(tmp_path):
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
    assert sidecar["attempt1_provenance"]["derived_template_id"] == templates["qwen_control"]["template_id"]
    assert sidecar["attempt1_provenance"]["derived_template_family"] == "qwen_control"
    assert sidecar["attempt1_input"]["model_files_sha256"] == inputs["qwen3.5-4b-base"]["model_files_sha256"]
    assert sidecar["inputs"]["child_report_sha256"] == hashlib.sha256((unit_dir / "report.json").read_bytes()).hexdigest()
    assert sidecar["inputs"]["authorization_amend_sha256"] == G.AUTHORIZATION_AMEND_SHA256
    assert sidecar["cost"] == {"gpu_seconds": 12.5}


# ------------------------------------------------------------------ M4 / BLOCKING-1: unit-start re-verification

def _campaign_inputs(root, tmp_path):
    provenance = G.build_attempt1_provenance(root)
    inputs = {base: G.attempt1_input(root, base) for base in A1_BASES}
    manifests = {base: G.read_json_finite(root / "EVIDENCE" / base / "final" / "manifest.json") for base in A1_BASES}
    kev_encoder = {"commit": KEV_COMMIT, "model_sha256": "a" * 64}
    templates = {family: G.template_block(family, manifests[base], inputs[base]["saved_describe"],
                                          kev_encoder=kev_encoder) for base, family in A1_BASES.items()}
    return provenance, inputs, manifests, kev_encoder, templates


def _snapshot_campaign(base: Path, monkeypatch, *, root_name=ROOT_NAME):
    """Host-shaped campaign start: the attempt-1 root's parent IS the runs dir, then a new root with the snapshot.

    On TASL-7 the attempt-1 root ``<runs>/p3a_operator_20261027`` makes ``<attempt1-root>/../gpu_lease_log.jsonl``
    exactly the global log ``R.LEASE_LOG`` that attempt 2's own child appends to; this reproduces that shape on CPU.
    """
    runs = base / "runs"
    monkeypatch.setenv("R1_RUNS", str(runs))
    attempt1 = make_attempt1_root(runs)
    provenance, inputs, manifests, kev_encoder, templates = _campaign_inputs(attempt1, base)
    new_root = runs / root_name
    new_root.mkdir(parents=True)
    snapshot = G.snapshot_attempt1_lease_log(new_root, provenance)
    provenance["lease_log_snapshot"] = snapshot
    verify = G.make_unit_start_verifier(attempt1, provenance, snapshot, inputs, manifests, templates, kev_encoder)
    return runs, attempt1, provenance, snapshot, verify


def test_blocking1_unit_start_verifies_the_immutable_snapshot_not_the_live_global_log(tmp_path, monkeypatch):
    runs, attempt1, provenance, snapshot, verify = _snapshot_campaign(tmp_path, monkeypatch)
    live = runs / G.LEASE_LOG_SNAPSHOT_NAME
    assert Path(snapshot["path"]) == (runs / ROOT_NAME / G.ATTEMPT1_PROVENANCE_DIRNAME / G.LEASE_LOG_SNAPSHOT_NAME)
    assert snapshot["sha256"] == provenance["lease_log_sha256"] == _sha(live)
    assert snapshot["bytes"] == live.stat().st_size and snapshot["lines"] == 2
    assert (Path(snapshot["path"]).stat().st_mode & 0o777) == 0o444          # read-only copy
    attempt1_before = G.hash_directory(attempt1)
    first = verify(label="DRYRUN", base="kev-0.8b")
    assert first["template_id"] == G.EXPECTED_DERIVED_TEMPLATE_IDS["kev"]
    assert first["lease_log_snapshot_sha256"] == snapshot["sha256"]
    # the DRYRUN child takes the GPU lease and appends its pair to the *live global* log (attempt-1 root's parent)
    with live.open("a") as fh:
        fh.write(json.dumps({"event": "start", "job": "probes", "pid": 900, "utc": "now",
                             "monotonic_s": 500.0}) + "\n")
        fh.write(json.dumps({"event": "end", "job": "probes", "pid": 900, "utc": "now",
                             "monotonic_s": 560.0}) + "\n")
    assert _sha(live) != provenance["lease_log_sha256"]                       # the pinned file grew
    second = verify(label="EVIDENCE", base="qwen3.5-4b-base")                 # BLOCKING-1: must still pass
    assert second["lease_log_snapshot_sha256"] == snapshot["sha256"]
    assert second["template_id"] == G.EXPECTED_DERIVED_TEMPLATE_IDS["qwen_control"]
    assert G.hash_directory(attempt1) == attempt1_before                      # attempt 1 is never written
    # a tampered snapshot is a STOP
    os.chmod(snapshot["path"], 0o644)
    Path(snapshot["path"]).write_bytes(Path(snapshot["path"]).read_bytes() + b'{"event": "end"}\n')
    with pytest.raises(G.R.TrackPStop, match="lease-log snapshot drift"):
        verify(label="EVIDENCE", base="qwen3.5-4b-base")


def test_snapshot_refuses_a_live_lease_log_that_changed_since_campaign_start(tmp_path, monkeypatch):
    runs = tmp_path / "runs"
    monkeypatch.setenv("R1_RUNS", str(runs))
    attempt1 = make_attempt1_root(runs)
    provenance = G.build_attempt1_provenance(attempt1)
    new_root = runs / ROOT_NAME
    new_root.mkdir(parents=True)
    with (runs / G.LEASE_LOG_SNAPSHOT_NAME).open("a") as fh:                  # race: live log changed first
        fh.write(json.dumps({"event": "note"}) + "\n")
    attempt1_before = G.hash_directory(attempt1)
    with pytest.raises(G.R.TrackPStop, match="changed between campaign start and the snapshot"):
        G.snapshot_attempt1_lease_log(new_root, provenance)
    assert not (new_root / G.ATTEMPT1_PROVENANCE_DIRNAME / G.LEASE_LOG_SNAPSHOT_NAME).exists()
    assert G.hash_directory(attempt1) == attempt1_before                     # attempt 1 not written by the failure


def test_unit_start_verifier_rehashes_attempt1_inputs_and_template(tmp_path, monkeypatch):
    _, root, provenance, snapshot, verify = _snapshot_campaign(tmp_path, monkeypatch)
    check = verify(label="DRYRUN", base="kev-0.8b")
    assert check["template_id"] == G.EXPECTED_DERIVED_TEMPLATE_IDS["kev"]
    assert len(check["journal_sha256"]) == 64 and len(check["attempt1_input_composite_sha256"]) == 64
    # a changed attempt-1 loaded file is caught before the child is spawned
    (root / "EVIDENCE" / "kev-0.8b" / "final" / "saved" / "heads.safetensors").write_bytes(b"tampered")
    with pytest.raises(G.R.TrackPStop, match="does not match|input drift"):
        verify(label="DRYRUN", base="kev-0.8b")
    # a changed journal is caught (immutable journal, not the live lease log)
    _, journal_root, provenance, snapshot, verify = _snapshot_campaign(tmp_path / "second", monkeypatch)
    (journal_root / "journal.jsonl").write_text((journal_root / "journal.jsonl").read_text() +
                                                json.dumps({"event": "note"}) + "\n")
    with pytest.raises(G.R.TrackPStop, match="provenance drift"):
        verify(label="DRYRUN", base="kev-0.8b")
    # a changed template declaration is caught
    _, _, provenance, snapshot, verify = _snapshot_campaign(tmp_path / "third", monkeypatch)
    monkeypatch.setattr(G, "TEMPLATE_ORDER", "proposal_first")
    with pytest.raises(G.R.TrackPStop, match="template drift"):
        verify(label="EVIDENCE", base="qwen3.5-4b-base")


# ------------------------------------------------------------------ M3: preflight internals

class _PreflightStubs:
    """Every live TASL-7 preflight dependency stubbed so one check can be isolated on CPU."""

    def __init__(self, monkeypatch, tmp_path):
        self.tmp_path = tmp_path
        self.paper = {"commit": "a" * 40, "branch": G.EXPECTED_PAPER_BRANCH, "dirty": False, "dirty_files": []}
        self.paper_identity = {"kind": "exact_reviewed_runner_commit", "commit": self.paper["commit"],
                               "branch": self.paper["branch"], "expected_commit": G.EXPECTED_PAPER_HEAD}
        self.head_error = None
        self.harness = {"commit": G.HARNESS_PIN, "branch": "main", "dirty": False, "dirty_files": []}
        self.base_ancestor = True
        self.e0 = tmp_path / "e0_v1.jsonl.gz"
        self.e0.write_bytes(b"e0")
        self.rule = tmp_path / "p3_rule_v2.yaml"
        self.rule.write_text("rule: v2\n")
        self.config = tmp_path / "trackp_portal.json"
        self.config.write_text('{"portal": 1}\n')
        self.freeze = tmp_path / "freeze.txt"
        self.freeze.write_text("torch==2.6.0\n")
        self.amend = tmp_path / "amend.md"                     # absent by default: file-present check skipped
        self.executing_error = None
        self.executing = {"repo": str(G.R.REPO), "runner_script_path": str(G.EXECUTING_RUNNER),
                          "runner_script_sha256": "a" * 64, "files": {}}
        self.git_show_bytes = self.config.read_bytes()
        self.freeze_text = self.freeze.read_text()
        self.ls_files_error = None
        self.hostname = "TASL-7"
        self.driver = {"boot_id": G.EXPECTED_ATTEMPT1_BOOT_ID, "nvidia_smi_driver": [G.EXPECTED_DRIVER]}
        self.disk_free = G.MIN_FREE_DISK_BYTES + 1
        self.gpu_census = []
        self.lease_free = True
        self.markers = []
        self.processes = []
        self.registry_bad = []

        monkeypatch.setattr(G, "E0_V1_PATH", str(self.e0))
        monkeypatch.setattr(G, "E0_V1_SHA256", _sha(self.e0))
        monkeypatch.setattr(G, "RULE_PATH", str(self.rule))
        monkeypatch.setattr(G, "RULE_SHA256", _sha(self.rule))
        monkeypatch.setattr(G, "CONFIG_PATH", str(self.config))
        monkeypatch.setattr(G, "CONFIG_APPROVED_COMMIT", "deadbee")
        monkeypatch.setattr(G, "FREEZE_PIN", str(self.freeze))
        monkeypatch.setattr(G, "AUTHORIZATION_AMEND_PATH", str(self.amend))
        monkeypatch.setattr(G, "verify_executing_files", self._verify_executing_files)
        monkeypatch.setattr(G.R, "git_commit", self._git_commit)
        monkeypatch.setattr(G, "is_ancestor", lambda commit, repo=None: self.base_ancestor)
        monkeypatch.setattr(G, "verify_paper_head", self._verify_paper_head)
        monkeypatch.setattr(G.subprocess, "run", self._subprocess_run)
        from r1.c3.train import registry
        monkeypatch.setattr(registry, "reverify", lambda path: list(self.registry_bad))
        monkeypatch.setattr(G.socket, "gethostname", lambda: self.hostname)
        monkeypatch.setattr(G.R, "tasl7_driver_snapshot", lambda: dict(self.driver))
        monkeypatch.setattr(G.shutil, "disk_usage",
                            lambda path: SimpleNamespace(free=self.disk_free, total=self.disk_free, used=0))
        monkeypatch.setattr(G.R, "foreign_compute_processes", lambda: list(self.gpu_census))
        monkeypatch.setattr(G, "lease_is_free", lambda: self.lease_free)
        monkeypatch.setattr(G, "priority_markers", lambda: list(self.markers))
        monkeypatch.setattr(G, "foreign_experiment_processes", lambda exclude=None: list(self.processes))
        monkeypatch.setattr(G, "verify_marker_helper", self._verify_marker_helper)

    def call(self, amend_sha256=None):
        return G.verify_probes_only_pins(amend_sha256 or G.AUTHORIZATION_AMEND_SHA256, disk_path=self.tmp_path)

    def _git_commit(self, repo):
        return dict(self.harness) if Path(repo) == G.R.harness_root() else dict(self.paper)

    def _verify_paper_head(self, paper, repo=None):
        if self.head_error is not None:
            raise G.R.TrackPStop(self.head_error)
        return dict(self.paper_identity)

    def _verify_marker_helper(self):
        return {"path": "/stub/trackp-evidence", "sha256": G.EXPECTED_MARKER_SHA256, "phase": G.MARKER_PHASE}

    def _verify_executing_files(self, repo=None):
        if self.executing_error is not None:
            raise G.R.TrackPStop(self.executing_error)
        return dict(self.executing)

    def _subprocess_run(self, command, **kwargs):
        if self.ls_files_error is not None and "ls-files" in command:
            raise self.ls_files_error
        if "show" in command:
            return SimpleNamespace(returncode=0, stdout=self.git_show_bytes, stderr=b"")
        if command and str(command[0]).endswith("/uv") or command and command[0] == "uv":
            return SimpleNamespace(returncode=0, stdout=self.freeze_text, stderr="")
        if "ls-files" in command:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        raise AssertionError(f"unexpected subprocess call: {command}")


def test_preflight_passes_with_every_live_check_stubbed(tmp_path, monkeypatch):
    stubs = _PreflightStubs(monkeypatch, tmp_path)
    pins = stubs.call()
    assert pins["boot_id"] == G.EXPECTED_ATTEMPT1_BOOT_ID == pins["attempt1_boot_id"]
    assert pins["boot_id_match"] is True and pins["paper_identity"]["kind"] == "exact_reviewed_runner_commit"
    assert len(pins["runner_script_sha256"]) == 64 and len(pins["child_script_sha256"]) == 64
    assert pins["executing_files"] == stubs.executing
    assert pins["authorization_amend_file_present"] is False


def test_preflight_refuses_wrong_head_or_paper_state(tmp_path, monkeypatch):
    stubs = _PreflightStubs(monkeypatch, tmp_path)
    stubs.paper["dirty"] = True
    with pytest.raises(G.R.TrackPStop, match="dirty"):
        stubs.call()
    stubs = _PreflightStubs(monkeypatch, tmp_path)
    stubs.head_error = "paper HEAD is not the reviewed runner commit"
    with pytest.raises(G.R.TrackPStop, match="not the reviewed runner commit"):
        stubs.call()
    stubs = _PreflightStubs(monkeypatch, tmp_path)
    stubs.base_ancestor = False
    with pytest.raises(G.R.TrackPStop, match="pinned base"):
        stubs.call()


def test_preflight_refuses_harness_pin_or_dirty(tmp_path, monkeypatch):
    stubs = _PreflightStubs(monkeypatch, tmp_path)
    stubs.harness["commit"] = "0" * 40
    with pytest.raises(G.R.TrackPStop, match="harness pin"):
        stubs.call()
    stubs = _PreflightStubs(monkeypatch, tmp_path)
    stubs.harness["dirty"] = True
    with pytest.raises(G.R.TrackPStop, match="harness pin"):
        stubs.call()


def test_preflight_refuses_e0_rule_config_freeze_registry(tmp_path, monkeypatch):
    cases = (("e0", b"changed", "authorized hash mismatch"),
             ("rule", b"changed", "authorized hash mismatch"),
             ("config", b'{"portal": 2}\n', "trackp_portal.json changed"),
             ("freeze", "torch==9.0\n", "freeze"),
             ("registry", ["model.bin"], "registered model files mismatch"))
    for attribute, value, match in cases:
        stubs = _PreflightStubs(monkeypatch, tmp_path)
        if attribute in ("e0", "rule"):
            getattr(stubs, attribute).write_bytes(value)
        elif attribute == "config":
            stubs.git_show_bytes = value
        elif attribute == "freeze":
            stubs.freeze_text = value
        else:
            stubs.registry_bad = value
        with pytest.raises(G.R.TrackPStop, match=match):
            stubs.call()


def test_preflight_refuses_executing_bytes_that_differ_from_head(tmp_path, monkeypatch):
    stubs = _PreflightStubs(monkeypatch, tmp_path)
    stubs.executing_error = ("executing file r1/scripts/trackp.py differs from HEAD:r1/scripts/trackp.py "
                             "(dirty/untracked/ignored working-tree difference)")
    with pytest.raises(G.R.TrackPStop, match="differs from HEAD"):
        stubs.call()


def test_preflight_refuses_host_driver_disk_and_boot_id(tmp_path, monkeypatch):
    stubs = _PreflightStubs(monkeypatch, tmp_path)
    stubs.hostname = "TASL-2"
    with pytest.raises(G.R.TrackPStop, match="TASL-7 only"):
        stubs.call()
    stubs = _PreflightStubs(monkeypatch, tmp_path)
    stubs.driver = {"boot_id": G.EXPECTED_ATTEMPT1_BOOT_ID, "nvidia_smi_driver": ["575.1.1"]}
    with pytest.raises(G.R.TrackPStop, match="NVIDIA driver"):
        stubs.call()
    stubs = _PreflightStubs(monkeypatch, tmp_path)
    stubs.driver = {"boot_id": G.EXPECTED_ATTEMPT1_BOOT_ID, "nvidia_smi_driver": []}
    with pytest.raises(G.R.TrackPStop, match="NVIDIA driver"):
        stubs.call()
    stubs = _PreflightStubs(monkeypatch, tmp_path)
    stubs.disk_free = 1
    with pytest.raises(G.R.TrackPStop, match="disk free"):
        stubs.call()
    stubs = _PreflightStubs(monkeypatch, tmp_path)
    stubs.driver = {"boot_id": "22222222-2222-2222-2222-222222222222",
                    "nvidia_smi_driver": [G.EXPECTED_DRIVER]}
    with pytest.raises(G.R.TrackPStop, match="unplanned reboot"):
        stubs.call()


def test_preflight_refuses_gpu_census_lease_marker_and_processes(tmp_path, monkeypatch):
    stubs = _PreflightStubs(monkeypatch, tmp_path)
    stubs.gpu_census = ["4242 python train.py"]
    with pytest.raises(G.R.TrackPStop, match="GPU compute census"):
        stubs.call()
    stubs = _PreflightStubs(monkeypatch, tmp_path)
    stubs.lease_free = False
    with pytest.raises(G.R.TrackPStop, match="lease"):
        stubs.call()
    stubs = _PreflightStubs(monkeypatch, tmp_path)
    stubs.markers = ["/home/dowling/r1_locks/p3a.active"]
    with pytest.raises(G.R.TrackPStop, match="evidence marker"):
        stubs.call()
    stubs = _PreflightStubs(monkeypatch, tmp_path)
    stubs.processes = ["4242 python -m r1.scripts.trackp probes"]
    with pytest.raises(G.R.TrackPStop, match="another experiment process"):
        stubs.call()


def test_preflight_refuses_helper_sha_untracked_scripts_and_amendment(tmp_path, monkeypatch):
    class Helper( _PreflightStubs):
        def _verify_marker_helper(self):
            raise G.R.TrackPStop("marker helper sha256 is not the reviewed one")

    with pytest.raises(G.R.TrackPStop, match="marker helper"):
        Helper(monkeypatch, tmp_path).call()
    stubs = _PreflightStubs(monkeypatch, tmp_path)
    stubs.ls_files_error = G.subprocess.CalledProcessError(1, ["git", "ls-files"])
    with pytest.raises(G.R.TrackPStop, match="not tracked"):
        stubs.call()
    stubs = _PreflightStubs(monkeypatch, tmp_path)
    stubs.amend.write_text("not the reviewed amendment\n")
    with pytest.raises(G.R.TrackPStop, match="amendment file"):
        stubs.call()
    stubs = _PreflightStubs(monkeypatch, tmp_path)
    stubs.amend.write_text("the reviewed amendment\n")
    digest = _sha(stubs.amend)
    monkeypatch.setattr(G, "AUTHORIZATION_AMEND_SHA256", digest)
    pins = G.verify_probes_only_pins(digest, disk_path=tmp_path)
    assert pins["authorization_amend_file_present"] is True and pins["authorization_amend_sha256"] == digest


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

def _stub_preflight_pins() -> dict:
    return {"boot_id": G.EXPECTED_ATTEMPT1_BOOT_ID, "attempt1_boot_id": G.EXPECTED_ATTEMPT1_BOOT_ID,
            "hostname": "TASL-7",
            "paper": {"commit": G.EXPECTED_PAPER_HEAD, "branch": G.EXPECTED_PAPER_BRANCH, "dirty": False},
            "paper_identity": {"kind": "exact_reviewed_runner_commit", "commit": G.EXPECTED_PAPER_HEAD,
                               "branch": G.EXPECTED_PAPER_BRANCH, "expected_commit": G.EXPECTED_PAPER_HEAD},
            "runner_script_path": str(G.EXECUTING_RUNNER),
            "runner_script_sha256": _sha(G.EXECUTING_RUNNER),
            "child_script_path": str(G.R.REPO / G.PAPER_CHILD_SCRIPT),
            "child_script_sha256": _sha(G.R.REPO / G.PAPER_CHILD_SCRIPT),
            "harness": {"commit": G.HARNESS_PIN},
            "marker": {"path": "helper", "sha256": G.EXPECTED_MARKER_SHA256, "phase": G.MARKER_PHASE},
            "authorization_amend_file_present": False}


def _campaign_fixture(tmp_path, monkeypatch):
    runs = _set_runs(monkeypatch, tmp_path)
    attempt1 = make_attempt1_root(runs)          # host shape: attempt-1 root's parent IS the runs dir
    monkeypatch.setattr(G, "attempt1_environment", lambda: {"PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"})
    monkeypatch.setattr(G, "verify_probes_only_pins", lambda amend, disk_path=None: _stub_preflight_pins())
    monkeypatch.setattr(G, "assert_attempt1_pins", lambda provenance: None)
    monkeypatch.setattr(G, "installed_kev_encoder",
                        lambda: {"commit": KEV_COMMIT, "model_sha256": "a" * 64})
    monkeypatch.setattr(G, "run_marker", lambda helper, action: {
        "command": [helper, action, G.MARKER_PHASE], "utc": "now", "rc": 0, "stdout": "", "stderr": ""})
    return attempt1


def test_campaign_runs_exactly_dryrun_then_evidence(tmp_path, monkeypatch):
    attempt1 = _campaign_fixture(tmp_path, monkeypatch)
    runs = _runs(tmp_path)
    live = runs / G.LEASE_LOG_SNAPSHOT_NAME
    lease_original = live.read_bytes()
    calls, sidecars = [], []

    def fake_run_unit(root, journal, boot_id, budget, label, base, name, arguments, gpu=True, **kw):
        verifier = kw.get("unit_start_verifier")
        start_check = verifier(label=label, base=base) if verifier is not None else None
        calls.append({"label": label, "base": base, "name": name, "arguments": list(arguments),
                      "template_id": kw.get("template_id"), "projection_seconds": kw.get("projection_seconds"),
                      "attempt1_input": kw.get("attempt1_input"), "unit_start_verification": start_check})
        if label == "DRYRUN":       # the DRYRUN child appends its lease pair to the live global log
            with live.open("a") as fh:
                fh.write(json.dumps({"event": "start", "pid": 77, "monotonic_s": 2000.0}) + "\n")
                fh.write(json.dumps({"event": "end", "pid": 77, "monotonic_s": 2010.0}) + "\n")
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
    assert calls[0]["unit_start_verification"]["template_id"] == calls[0]["template_id"]
    assert calls[1]["unit_start_verification"]["template_id"] == calls[1]["template_id"]
    assert calls[1]["attempt1_input"]["loaded_artifact"].endswith("qwen3.5-4b-base/final/saved")
    assert [sidecar["schema"] for sidecar in sidecars] == [G.UNIT_MANIFEST_SCHEMA] * 2
    assert [sidecar["attempt1_provenance"]["derived_template_id"] for sidecar in sidecars] == [
        G.EXPECTED_DERIVED_TEMPLATE_IDS["kev"], G.EXPECTED_DERIVED_TEMPLATE_IDS["qwen_control"]]
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
    # MAJOR-1/MAJOR-2: expected and actual boot ids, exact paper HEAD and executing-script hashes are recorded
    assert start["boot_id"] == G.EXPECTED_ATTEMPT1_BOOT_ID
    assert start["expected_attempt1_boot_id"] == G.EXPECTED_ATTEMPT1_BOOT_ID == start["attempt1_boot_id"]
    assert start["paper_head"] == G.EXPECTED_PAPER_HEAD and start["paper_identity"]["kind"] == "exact_reviewed_runner_commit"
    assert start["attempt1_boot_id_match"] is True               # MINOR-5: a computed comparison, not a literal
    # BLOCKING-1: the campaign snapshotted the attempt-1 lease log read-only before any unit, and the EVIDENCE
    # unit-start verifier still passed after the DRYRUN appended to the live global log
    snapshot = start["attempt1_provenance"]["lease_log_snapshot"]
    snapshot_path = Path(snapshot["path"])
    assert snapshot_path == args.root / G.ATTEMPT1_PROVENANCE_DIRNAME / G.LEASE_LOG_SNAPSHOT_NAME
    assert snapshot_path.read_bytes() == lease_original and snapshot["sha256"] == _sha(snapshot_path)
    assert (snapshot_path.stat().st_mode & 0o777) == 0o444
    assert snapshot["sha256"] == start["attempt1_provenance"]["lease_log_sha256"]
    assert _sha(live) != snapshot["sha256"]                     # the live global log grew during the campaign
    assert calls[0]["unit_start_verification"]["lease_log_snapshot_sha256"] == snapshot["sha256"]
    assert calls[1]["unit_start_verification"]["lease_log_snapshot_sha256"] == snapshot["sha256"]
    assert start["runner_script_sha256"] == _sha(G.EXECUTING_RUNNER)
    assert start["child_script_sha256"] == _sha(G.R.REPO / G.PAPER_CHILD_SCRIPT)
    unit_events = [event for event in events if event["event"] in ("unit_start", "unit_complete")]
    assert all("template_id" in event for event in unit_events)
    assert all("unit_start_verification" in event for event in unit_events if event["event"] == "unit_start")
    assert (args.root / "gpu_lease_log.jsonl").exists()             # the new root gets its own lease log
    assert events[-1]["budget"]["new_lease_seconds"] == pytest.approx(20.0)   # recorded, and added to attempt 1
    assert events[-1]["budget"]["cap_seconds"] == 60 * 3600


def test_campaign_stops_before_root_if_the_boot_id_is_not_the_attempt1_boot(tmp_path, monkeypatch):
    _campaign_fixture(tmp_path, monkeypatch)
    pins = _stub_preflight_pins()
    pins["boot_id"] = "33333333-3333-3333-3333-333333333333"
    monkeypatch.setattr(G, "verify_probes_only_pins", lambda amend, disk_path=None: pins)
    args = _ns(tmp_path)
    with pytest.raises(G.R.TrackPStop, match="unplanned reboot"):
        G.run_probes_only_campaign(args)
    assert not args.root.exists()                                    # STOP before root creation / marker


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


def test_run_unit_unit_start_verifier_stops_before_any_child(tmp_path, monkeypatch):
    def fake_verifier(*, label, base):
        raise G.R.TrackPStop(f"template drift at {label}/{base} unit start")

    monkeypatch.setattr(G.R, "tasl7_driver_snapshot", lambda: {"boot_id": "boot"})
    monkeypatch.setattr(G, "verify_live_pins", lambda journal: None)
    root = tmp_path / "campaign"
    root.mkdir()
    with pytest.raises(G.R.TrackPStop, match="template drift"):
        G.run_unit(root, root / "journal.jsonl", "boot", G.GPUBudget(lease_log=tmp_path / "lease"),
                   "DRYRUN", "kev", "probes", [], gpu=False, unit_start_verifier=fake_verifier)
    assert not (root / "journal.jsonl").exists() and not (root / "DRYRUN").exists()


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
