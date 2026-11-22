"""The D4 option-B contingency of the sweep-2 audit (``r1.c3.audit_d4b``, R1-BX-PROPOSED-CONFIRM REVISIONS (c)): OFF by
default and refused without its author row; with a test row, divergent and partial labels as E5 defines them; the
default D4 A path unchanged. Synthetic only; no label or evaluation file of a real audit is opened. AI-assisted."""
from __future__ import annotations

import hashlib
import json
import math
import shutil
from pathlib import Path

import pytest

from r1.c3 import audit, audit_d4b as X, dataset as D, sweep2_batch as SB

STOP_REASON = "invalid audit result for openml_wdbc/" + "a" * 64
RUNTIME = None


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _plan_text(stop_sha: str | None, *, rows: int = 1, row_id: str = X.D4B_ROW, run_id: str = SB.RUN_ID) -> str:
    """A PLAN §10 with a dated author table (the R1-SWEEP2-B2-D4B row only when ``stop_sha`` is given)."""
    body = "## 10. Decisions\n\n### Author decisions, 23 November 2026\n\n| ID | Author decision |\n|---|---|\n" \
           "| R1-OTHER | something else |\n"
    if stop_sha is not None:
        body += "".join(f"| {row_id} | After the D4 STOP of {run_id} (STOP.json sha256 {stop_sha}), the sweep-2 audit "
                        f"uses R1-BX-PROPOSED-CONFIRM REVISIONS (c). |\n" for _ in range(rows))
    return body


def _stopped(paper: Path, reason: str = STOP_REASON, source: str = "sweep2", completed: bool = False) -> Path:
    d = paper / "results/r1/evidence/C3_audit_EVIDENCE_20991231T000000Z"
    d.mkdir(parents=True)
    (d / "STOP.json").write_text(json.dumps({"label": "EVIDENCE", "reason": reason, "unscheduled": 3}))
    (d / "environment.json").write_text(json.dumps({"source": source}))
    if completed:
        (d / "evidence_completion.json").write_text("{}")
    return d


# ------------------------------------------------------------------------------------------------- divergence
@pytest.mark.parametrize("row,divergent", [
    ({"success": True, "changed_files": False, "metric": float("nan")}, True),      # non-finite metric
    ({"success": True, "changed_files": False, "metric": None}, True),              # no metric at the budget
    ({"success": False, "changed_files": False, "metric": None, "failure": "exit code 1"}, True),
    ({"success": False, "changed_files": False, "metric": None, "failure": "exit code -6"}, True),
    ({"success": False, "changed_files": False, "metric": None, "failure": "run_command timed out after 600s"}, False),
    ({"success": False, "changed_files": False, "metric": None, "failure": "run_command raised OSError: x"}, False),
    ({"success": True, "changed_files": True, "metric": None}, False),              # a changed file is never divergence
    ({"success": True, "changed_files": False, "metric": 0.9}, False),              # a valid run
])
def test_divergence_reading(row, divergent):
    assert X.is_divergent(row) is divergent


def test_run_config_seed_rule():
    """D4 A: any failed, file-changing or non-finite seed run ends the configuration; the contingency continues only
    past a divergent one."""
    ok = {"success": True, "changed_files": False, "metric": 0.9}
    nan = {"success": True, "changed_files": False, "metric": float("nan")}
    exit1 = {"success": False, "changed_files": False, "metric": None, "failure": "exit code 1"}
    timeout = {"success": False, "changed_files": False, "metric": None, "failure": "run_command timed out after 600s"}
    changed = {"success": True, "changed_files": True, "metric": 0.9}
    assert [audit._seed_ends_config(r) for r in (ok, nan, exit1, timeout, changed)] == [False, True, True, True, True]
    assert [audit._seed_ends_config(r, True) for r in (ok, nan, exit1, timeout, changed)] == \
        [False, False, False, True, True]


def test_e5_block_labels():
    seeds = [7001, 7002, 7003, 7004, 7005]
    inc = [0.80, 0.81, 0.82, 0.83, 0.84]
    full = X.block_label([0.90, 0.91, 0.92, 0.93, 0.94], inc, seeds)
    assert not full["partial"] and full["k"] == 5 and math.isclose(full["delta"], 0.10)
    one = X.block_label([0.90, None, 0.92, 0.93, 0.94], inc, seeds)          # mu from the rest, marked partial
    assert one["partial"] and one["k"] == 4 and one["candidate_diverged_seeds"] == [7002]
    assert math.isclose(one["delta"], 0.10) and one["se"] is not None
    two = X.block_label([None, None, 0.92, 0.93, 0.95], inc, seeds)          # 2 of 5: still partial
    assert two["partial"] and two["k"] == 3 and math.isclose(two["delta"], (0.10 + 0.10 + 0.11) / 3)
    three = X.block_label([None, None, None, 0.93, 0.94], inc, seeds)       # more than half: divergent
    assert three["divergent"] and three["candidate_diverged_seeds"] == [7001, 7002, 7003]
    inc_lost = X.block_label([0.90, 0.91, 0.92, 0.93, 0.94], [None, 0.81, 0.82, 0.83, 0.84], seeds)
    assert inc_lost["partial"] and inc_lost["k"] == 4 and inc_lost["incumbent_diverged_seeds"] == [7001]
    with pytest.raises(ValueError, match="fewer than two usable"):           # an incumbent's divergence is a STOP
        X.block_label([0.90, 0.91, 0.92, 0.93, 0.94], [None, None, None, None, 0.84], seeds)


# ------------------------------------------------------------------------------------------------- enabling
def test_contingency_is_off_without_its_author_row(tmp_path, monkeypatch):
    paper = tmp_path / "paper"
    stopped = _stopped(paper)
    stop_sha = _sha((stopped / "STOP.json").read_bytes())
    plan = {"docs/r1/PLAN.md": _plan_text(None).encode()}
    monkeypatch.setattr(audit, "_published_bytes", lambda root, rel: plan[rel])
    rel = stopped.relative_to(paper)
    with pytest.raises(ValueError, match="D4B is OFF"):
        X.check_contingency(paper, rel)
    for text in (_plan_text("0" * 64),                                   # names another STOP
                 _plan_text(stop_sha, rows=2),                           # two rows
                 _plan_text(stop_sha, run_id="s2ev-other"),              # another run
                 "```\n" + _plan_text(stop_sha) + "```\n"):              # only inside a fenced block
        plan["docs/r1/PLAN.md"] = text.encode()
        with pytest.raises(ValueError, match="D4B is OFF"):
            X.check_contingency(paper, rel)
    plan["docs/r1/PLAN.md"] = _plan_text(stop_sha).encode()
    record = X.check_contingency(paper, rel)
    assert record["stop_sha256"] == stop_sha and record["row"] == "R1-SWEEP2-B2-D4B" and record["stopped_audit"] == str(rel)


@pytest.mark.parametrize("kind,match", [
    ("reason", "not a seed-run STOP"),
    ("source", "not a sweep-2 audit"),
    ("completed", "or completed"),
    ("path", "must be results/r1/evidence"),
])
def test_contingency_needs_a_sweep2_seed_run_stop(tmp_path, monkeypatch, kind, match):
    paper = tmp_path / "paper"
    stopped = _stopped(paper, reason="audit deadline exceeded" if kind == "reason" else STOP_REASON,
                       source="sweep1" if kind == "source" else "sweep2", completed=kind == "completed")
    stop_sha = _sha((stopped / "STOP.json").read_bytes())
    monkeypatch.setattr(audit, "_published_bytes", lambda root, rel: _plan_text(stop_sha).encode())
    rel = Path("results/r1/other/x") if kind == "path" else stopped.relative_to(paper)
    with pytest.raises(ValueError, match=match):
        X.check_contingency(paper, rel)


# ------------------------------------------------------------------------------------------------- evidence run
def _world(tmp_path, monkeypatch, metric, *, d4b=None, stop_sha=None):
    """The synthetic sweep-2 evidence run of test_c3_sweep2_audit, with per-seed metrics from ``metric(key, seed)``
    (None, a float, or nan). The pool records the keyword arguments run_config receives."""
    monkeypatch.setattr(audit, "b2_addendum", lambda *a: {"path": "docs/r1/authorizations/x.md", "sha256": "addendum"})
    monkeypatch.setattr(audit, "sweep2_harness_equivalence",
                        lambda h: {"diff": "empty", "paths": list(audit.SWEEP2_EQUAL_PATHS)})
    monkeypatch.setattr(audit, "_sweep2_pins_match", lambda *a: None)
    table = tmp_path / "table"
    table.mkdir(parents=True)
    for name, data in [("build.json", "{}"), ("proposals.jsonl", "{}\n"),
                       ("configs.json", json.dumps({"c": {"files": {}}, "i": {"files": {}}}))]:
        (table / name).write_text(data)
    (tmp_path / SB.AUTHORIZATION["path"]).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / SB.AUTHORIZATION["path"]).write_text("auth")
    index = tmp_path / "index"
    index.write_text("index")
    rows = [{"proposal_id": "p", "node": "n", "noop": False, "duplicate": False, "sigma_node": 0.5}]
    monkeypatch.setattr(D, "load_table", lambda _: rows)
    plan = [{"proposal_id": "p", "node": "n", "candidate_hash": "c", "incumbent_hash": "i"}]
    env = {"worker_python": "/venv/bin/python3", "worker_prefix": "/venv",
           "worker_versions": {"scikit-learn": "1.8.0", "numpy": "2.4.4", "pandas": "3.0.3", "scipy": "1.17.1"},
           "package_list_sha256": "abc", "harness_root": "/h", "environment_basis": {},
           "harness_untracked": {"data_caches_sha256": {"n": "d"}}}
    monkeypatch.setattr(audit, "evidence_environment", lambda *a: dict(env))
    monkeypatch.setattr(audit, "harness_untracked_state", lambda *a: {"data_caches_sha256": {"n": "d"}})
    monkeypatch.setattr(audit, "evidence_paper_provenance", lambda *a: {})
    binding = {"counts": {"eligible": 1, "noops": 0, "duplicates": 0}, "source": "sweep2", "extract_sha256": "e" * 64}
    monkeypatch.setattr(audit, "evidence_plan", lambda *a: (plan, binding))
    monkeypatch.setattr(audit, "evidence_resources", lambda *a: {})
    monkeypatch.setattr(audit, "monitor_evidence_resources", lambda *a: {})
    seen = []
    runtime = {"worker_python": env["worker_python"], "prefix": env["worker_prefix"], "base_prefix": "/s",
               "versions": env["worker_versions"], "package_list_sha256": env["package_list_sha256"],
               "worker_command_python": "/w/python3", "worker_python_realpath": "/s/python3"}

    class Future:
        def __init__(self, key): self.key = key
        def result(self):
            out = []
            for s in audit.DEFAULT_SEEDS:
                m = metric(self.key, s)
                ok = m is not None and math.isfinite(m)
                out.append({"seed": s, "success": True, "changed_files": False, "metric": m if ok else None,
                            "wall_seconds": 1.0, "worker_runtime": runtime})
            return out

    class Pool:
        def __init__(self, **kw): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def submit(self, fn, node, files, seeds, scratch, stop, journal, identity, **kw):
            seen.append(kw)
            return Future(identity["config_hash"])
    monkeypatch.setattr(audit, "ProcessPoolExecutor", Pool)
    monkeypatch.setattr(audit, "wait", lambda pending, **kw: ({pending[0]}, set(pending[1:])))
    out = tmp_path / "results/r1/evidence/C3_audit_EVIDENCE_new"
    try:
        audit.evidence_run(table, tmp_path, index, None, out, 1, 300, scratch_root=tmp_path / "scratch",
                           source="sweep2", d4b_after_stop=d4b)
    finally:
        if (tmp_path / "scratch").exists():
            shutil.rmtree(tmp_path / "scratch")         # local fixture scratch only
    return out, seen


def _metric_with_divergence(key, seed):
    base = 0.80 + (seed - 7001) * 0.001
    if key == "c":
        return float("nan") if seed == 7002 else base + 0.1
    return base


def test_default_d4a_still_stops_on_a_divergent_seed_run(tmp_path, monkeypatch):
    """D4 A unchanged: one NaN seed run STOPs the audit (STOP.json, no blocks), and run_config gets no new keyword."""
    with pytest.raises(ValueError, match="invalid audit result for n/c"):
        _world(tmp_path, monkeypatch, _metric_with_divergence)
    out = tmp_path / "results/r1/evidence/C3_audit_EVIDENCE_new"
    assert json.loads((out / "STOP.json").read_text())["reason"].startswith("invalid audit result for n/")
    assert not (out / "label_block.jsonl").exists() and "d4b_contingency" not in json.loads(
        (out / "environment.json").read_text())


def test_default_d4a_complete_run_unchanged(tmp_path, monkeypatch):
    out, seen = _world(tmp_path, monkeypatch, lambda k, s: 0.8 + (0.1 if k == "c" else 0) + (s - 7001) * 0.001)
    completion = json.loads((out / "evidence_completion.json").read_text())
    assert completion["schema"] == audit.SWEEP2_COMPLETION_SCHEMA and "d4b_contingency" not in completion
    assert all(kw == {} for kw in seen)
    label = json.loads((out / "label_block.jsonl").read_text().splitlines()[0])
    assert label["label_kind"] == "audit" and "partial" not in label


def test_contingency_refused_without_the_row_before_anything_is_written(tmp_path, monkeypatch):
    stopped = _stopped(tmp_path)
    monkeypatch.setattr(audit, "_published_bytes", lambda root, rel: _plan_text(None).encode())
    with pytest.raises(ValueError, match="D4B is OFF"):
        _world(tmp_path, monkeypatch, _metric_with_divergence, d4b=stopped.relative_to(tmp_path))
    assert not (tmp_path / "results/r1/evidence/C3_audit_EVIDENCE_new").exists()


def test_contingency_with_a_test_row_writes_partial_labels(tmp_path, monkeypatch):
    stopped = _stopped(tmp_path)
    stop_sha = _sha((stopped / "STOP.json").read_bytes())
    monkeypatch.setattr(audit, "_published_bytes", lambda root, rel: _plan_text(stop_sha).encode())
    out, seen = _world(tmp_path, monkeypatch, _metric_with_divergence, d4b=stopped.relative_to(tmp_path))
    assert all(kw == {"continue_on_divergence": True} for kw in seen) and seen
    label = json.loads((out / "label_block.jsonl").read_text().splitlines()[0])
    assert label["label_kind"] == "audit_partial" and label["partial"] and label["k_label"] == 4
    assert label["candidate_diverged_seeds"] == [7002] and math.isclose(label["delta_label"], 0.1)
    assert label["soft_parameters"]["k_label"] == 4
    evaluation = json.loads((out / "evaluation_block.jsonl").read_text().splitlines()[0])
    assert evaluation["partial"] is False and evaluation["k_evaluation"] == 5
    completion = json.loads((out / "evidence_completion.json").read_text())
    assert completion["schema"] == X.D4B_COMPLETION_SCHEMA
    assert completion["d4b_contingency"]["stop_sha256"] == stop_sha
    assert completion["d4b_contingency"]["counts"] == {"divergent": 0, "partial": 1, "complete": 0, "rule_noop": 0}
    env = json.loads((out / "environment.json").read_text())
    assert env["d4b_contingency"]["row"] == X.D4B_ROW
    # the release integrity check accepts only /4: a contingency completion is not consumable as it stands
    from r1.c3 import release_checks
    monkeypatch.setattr(audit, "verify_evidence_completion", lambda *a, **k: completion)
    monkeypatch.setattr(release_checks, "_sweep2_batch_published", lambda: None)
    with pytest.raises(ValueError, match="not a sweep-2 audit completion"):
        release_checks.sweep2_integrity(out, out, paper_root=tmp_path, index=tmp_path / "index")


def test_contingency_divergent_proposal(tmp_path, monkeypatch):
    stopped = _stopped(tmp_path)
    stop_sha = _sha((stopped / "STOP.json").read_bytes())
    monkeypatch.setattr(audit, "_published_bytes", lambda root, rel: _plan_text(stop_sha).encode())

    def metric(key, seed):
        if key == "c" and seed in (7001, 7003, 7005):
            return None
        return 0.8 + (0.1 if key == "c" else 0)
    out, _ = _world(tmp_path, monkeypatch, metric, d4b=stopped.relative_to(tmp_path))
    label = json.loads((out / "label_block.jsonl").read_text().splitlines()[0])
    assert label["label_kind"] == "divergent" and label["delta_label"] is None and label["soft_parameters"] is None
    assert label["action_target_rule"].startswith("u = -g")
    completion = json.loads((out / "evidence_completion.json").read_text())
    assert completion["d4b_contingency"]["counts"]["divergent"] == 1


def test_contingency_still_stops_on_a_non_divergent_failure(tmp_path, monkeypatch):
    stopped = _stopped(tmp_path)
    stop_sha = _sha((stopped / "STOP.json").read_bytes())
    monkeypatch.setattr(audit, "_published_bytes", lambda root, rel: _plan_text(stop_sha).encode())
    orig = X.is_divergent
    monkeypatch.setattr(X, "is_divergent", lambda row: False if row.get("metric") is None else orig(row))
    with pytest.raises(ValueError, match="invalid audit result"):
        _world(tmp_path, monkeypatch, _metric_with_divergence, d4b=stopped.relative_to(tmp_path))


def test_contingency_is_sweep2_only(tmp_path):
    with pytest.raises(ValueError, match="sweep-2 audit only"):
        audit.evidence_run(tmp_path, tmp_path, tmp_path, tmp_path, tmp_path / "o", 1, 10, source="sweep1",
                           d4b_after_stop=tmp_path)
