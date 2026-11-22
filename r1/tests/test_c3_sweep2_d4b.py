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


def _stopped(paper: Path, reason: str = STOP_REASON, source: str = "sweep2", completed: bool = False,
             contingency: bool = False) -> Path:
    d = paper / "results/r1/evidence/C3_audit_EVIDENCE_20991231T000000Z"
    d.mkdir(parents=True)
    (d / "STOP.json").write_text(json.dumps({"label": "EVIDENCE", "reason": reason, "unscheduled": 3}))
    (d / "environment.json").write_text(json.dumps({"source": source,
                                                    **({"d4b_contingency": {"row": X.D4B_ROW}} if contingency else {})}))
    if completed:
        (d / "evidence_completion.json").write_text("{}")
    return d


# ------------------------------------------------------------------------------------------------- divergence
NAN_TAIL = "Traceback ...\nValueError: Input X contains NaN.\nFAILURE_CATEGORY=runtime_error\n"


def _failed(failure, **kw):
    return {"success": False, "changed_files": False, "metric": None, "failure": failure, **kw}


@pytest.mark.parametrize("row,divergent", [
    ({"success": True, "changed_files": False, "metric": float("nan")}, True),      # non-finite metric
    ({"success": True, "changed_files": False, "metric": None}, True),              # no metric at the budget
    (_failed("exit code 1", log_tail="loss became nan at step 40\n"), True),        # exit 1, non-finite named
    (_failed("exit code 1", failure_category="runtime_error", log_tail=NAN_TAIL), True),
    (_failed("exit code 1", log_tail="RuntimeError: weights are non-finite"), True),
    (_failed("exit code 1", log_tail="FileNotFoundError: data_cache/x.parquet"), False),   # no non-finite value
    (_failed("exit code 1"), False),                                                 # no log tail recorded
    (_failed("exit code 1", log_tail=""), False),                                    # unreadable log
    (_failed("exit code 1", log_tail="banana information"), False),                  # words are matched whole
    (_failed("exit code 1", failure_category="invalid_config", log_tail="nan"), False),
    (_failed("exit code 2", log_tail="nan"), False),                                 # a configuration rejection
    (_failed("exit code -6", log_tail="nan"), False),                                # a signal (SIGABRT)
    (_failed("exit code -9", log_tail="nan"), False),                                # SIGKILL
    (_failed("exit code 137", log_tail="nan"), False),                               # an OOM kill through the shell
    (_failed("run_command timed out after 600s", log_tail="nan"), False),
    (_failed("run_command raised OSError: x", log_tail="nan"), False),
    ({"success": True, "changed_files": True, "metric": None}, False),              # a changed file is never divergence
    (_failed("exit code 1", changed_files=True, log_tail="nan"), False),
    ({"success": True, "changed_files": False, "metric": 0.9}, False),              # a valid run
])
def test_divergence_reading(row, divergent):
    assert X.is_divergent(row) is divergent


def test_diagnostics_record_the_category_and_the_log_tail(tmp_path):
    from types import SimpleNamespace
    log = tmp_path / "run.log"
    log.write_text("x" * 5000 + NAN_TAIL)
    failed = SimpleNamespace(success=False, raw_log_ref=str(log), extra={"failure_category": "runtime_error"})
    d = X.diagnostics(failed)
    assert d["failure_category"] == "runtime_error" and d["log_tail"].endswith(NAN_TAIL)
    assert len(d["log_tail"]) == X.LOG_TAIL_CHARS
    assert X.diagnostics(SimpleNamespace(success=False, raw_log_ref=str(tmp_path / "gone"), extra={})) == \
        {"log_tail": ""}
    assert X.diagnostics(SimpleNamespace(success=True, raw_log_ref=str(log), extra={})) == {}


def test_run_config_seed_rule():
    """D4 A: any failed, file-changing or non-finite seed run ends the configuration; the contingency continues only
    past a divergent one."""
    ok = {"success": True, "changed_files": False, "metric": 0.9}
    nan = {"success": True, "changed_files": False, "metric": float("nan")}
    exit1 = _failed("exit code 1", log_tail=NAN_TAIL)
    exit1_plain = _failed("exit code 1", log_tail="KeyError: 'x'")
    timeout = _failed("run_command timed out after 600s")
    changed = {"success": True, "changed_files": True, "metric": 0.9}
    rows = (ok, nan, exit1, exit1_plain, timeout, changed)
    assert [audit._seed_ends_config(r) for r in rows] == [False, True, True, True, True, True]
    assert [audit._seed_ends_config(r, True) for r in rows] == [False, False, False, True, True, True]


def test_run_config_gives_the_next_seed_a_fresh_node_after_a_divergent_run(tmp_path, monkeypatch):
    """With ``continue_on_divergence`` the rows carry the diagnostics, a divergent run does not end the configuration,
    and the next seed runs in a fresh copy (the used copy is kept, renamed); a non-divergent failure still ends it."""
    from types import SimpleNamespace
    from r1 import harness
    try:
        harness.import_harness()                 # the real harness's src on sys.path (its worker classes are faked)
    except RuntimeError:
        pytest.skip("no harness checkout (AR_HARNESS_ROOT)")
    harness_root = tmp_path / "harness"
    (harness_root / "nodes" / "node").mkdir(parents=True)
    (harness_root / "nodes" / "node" / "code.py").write_text("original")
    monkeypatch.setattr(harness, "import_harness", lambda: harness_root)
    import autoresearch.nodes.registry as registry
    import autoresearch.worker.local_worker as local_worker
    monkeypatch.setattr(registry, "load_registered_node",
                        lambda *a, **k: SimpleNamespace(editable_paths=["code.py"], metric_name="m", run_command="x"))
    monkeypatch.setattr(audit, "worker_runtime", lambda *a: {"w": 1})
    script = {"rows": []}

    class FakeWorker:
        def __init__(self, node_root, artifact_dir, **kwargs):
            self.root = Path(node_root)

        def run_trial_at_seed(self, proposal, spec, i, *, train_seed, split_seed):
            (self.root / "artifacts").mkdir(exist_ok=True)
            seen = sorted(p.name for p in (self.root / "artifacts").iterdir())
            (self.root / "artifacts" / f"seed{train_seed}").write_text("x")
            kind = script["rows"][i - 1]
            log = tmp_path / f"log{train_seed}"
            log.write_text(NAN_TAIL if kind == "nan" else "KeyError\n")
            script.setdefault("seen", []).append(seen)
            if kind == "ok":
                return SimpleNamespace(success=True, failure_message=None, parsed_metrics={"m": 0.9}, changed_files=[],
                                       raw_log_ref=str(log), extra={})
            return SimpleNamespace(success=False, failure_message="exit code 1", parsed_metrics={}, changed_files=[],
                                   raw_log_ref=str(log), extra={"failure_category": "runtime_error"})
    monkeypatch.setattr(local_worker, "LocalWorker", FakeWorker)
    script["rows"] = ["ok", "nan", "ok"]
    work_parent = tmp_path / "w1"
    work_parent.mkdir()
    rows = audit.run_config("node", {"code.py": "changed"}, [1, 2, 3], str(work_parent), True,
                            continue_on_divergence=True)
    assert [r["success"] for r in rows] == [True, False, True] and rows[1]["log_tail"] == NAN_TAIL
    assert rows[1]["failure_category"] == "runtime_error" and "log_tail" not in rows[0]
    assert script["seen"] == [[], ["seed1"], []]                     # seed 3 ran in a fresh copy
    work = next(work_parent.iterdir())
    assert sorted(p.name for p in work.iterdir() if p.name.startswith("node")) == ["node", "node.diverged_seed2"]
    assert (work / "node" / "code.py").read_text() == "changed"
    script.update(rows=["ok", "plain", "ok"], seen=[])
    work_parent = tmp_path / "w2"
    work_parent.mkdir()
    rows = audit.run_config("node", {"code.py": "changed"}, [1, 2, 3], str(work_parent), True,
                            continue_on_divergence=True)
    assert len(rows) == 2                                             # a non-divergent failure ends the configuration
    script.update(rows=["ok", "nan", "ok"], seen=[])
    work_parent = tmp_path / "w3"
    work_parent.mkdir()
    rows = audit.run_config("node", {"code.py": "changed"}, [1, 2, 3], str(work_parent), True)
    assert len(rows) == 2 and "log_tail" not in rows[1]               # D4 A: unchanged rows, ends at the failure


def test_e5_block_labels():
    seeds = [7001, 7002, 7003, 7004, 7005]
    inc = [0.80, 0.81, 0.82, 0.83, 0.84]
    full = X.block_label([0.90, 0.91, 0.92, 0.93, 0.94], inc, seeds)
    assert not full["partial"] and full["k"] == 5 and math.isclose(full["delta"], 0.10) and full["divergent_seeds"] == []
    one = X.block_label([0.90, None, 0.92, 0.93, 0.94], inc, seeds)          # mu from the rest, marked partial
    assert one["partial"] and one["k"] == 4 and one["divergent_seeds"] == [7002]
    assert math.isclose(one["delta"], 0.10) and one["se"] is not None
    two = X.block_label([None, None, 0.92, 0.93, 0.95], inc, seeds)          # 2 of 5: still partial, k = 3
    assert two["partial"] and two["k"] == 3 and math.isclose(two["delta"], (0.10 + 0.10 + 0.11) / 3)
    three = X.block_label([None, None, None, 0.93, 0.94], inc, seeds)       # more than half: divergent
    assert three["divergent"] and three["divergent_seeds"] == [7001, 7002, 7003]
    for inc_lost in ([None, 0.81, 0.82, 0.83, 0.84], [0.80, 0.81, 0.82, 0.83, None]):
        with pytest.raises(ValueError, match="incumbent diverged"):        # an incumbent's divergence is a STOP
            X.block_label([0.90, 0.91, 0.92, 0.93, 0.94], inc_lost, seeds)
    with pytest.raises(ValueError, match="incumbent diverged"):            # the old k = 2 case cannot arise
        X.block_label([None, None, 0.9, 0.9, 0.9], [0.8, 0.8, None, 0.8, 0.8], seeds)


@pytest.mark.parametrize("cand,label,evaluation", [
    ([0.9] * 10, ("audit", 5), ("complete", None)),
    ([0.9, None, 0.9, 0.9, 0.9] + [0.9] * 5, ("audit", 4), ("complete", None)),
    ([None, 0.9, None, 0.9, 0.9] + [0.9] * 5, ("audit", 3), ("complete", None)),
    ([None, None, None, 0.9, 0.9] + [0.9] * 5, ("divergent", None), ("complete", None)),
    ([0.9] * 5 + [0.9, None, 0.9, 0.9, 0.9], ("audit", 5), ("partial", [7007])),
    ([0.9] * 5 + [None, None, None, 0.9, 0.9], ("audit", 5), ("divergent", [7006, 7007, 7008])),
])
def test_rows_have_the_frozen_gate_input_builder_shapes(monkeypatch, cand, label, evaluation):
    """PRE-DIV A as the signed preregistration pins it: the frozen builder (sha256 in the preregistration) accepts the
    contingency's label and evaluation rows and reads them as complete, partial or divergent; complete rows are D4 A's
    rows exactly (same keys); label rows carry only the reader's keys."""
    from r1.c3 import gate_input_builder as B
    from r1.c3.train import sft_data
    prereg = (Path(__file__).resolve().parents[2] / "docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md")
    assert f"gate_input_builder_sha256: {_sha(Path(B.__file__).read_bytes())}" in prereg.read_text()
    row = {"proposal_id": "p", "node": "n", "noop": False, "duplicate": False, "sigma_node": 0.5}
    monkeypatch.setattr(D, "load_table", lambda _: [row])
    inc = [0.80, 0.81, 0.82, 0.83, 0.84] * 2
    res = [{"proposal_id": "p", "node": "n", "reason": None, "candidate_hash": "c", "incumbent_hash": "i",
            "seeds": list(audit.DEFAULT_SEEDS), "candidate_metrics": cand, "incumbent_metrics": inc}]
    labels, evaluations = X.blocks("unused", res)
    lab, ev = labels[0], evaluations[0]
    assert B._label_ok(lab, row, B.T0_LABEL_SEEDS) == label[0]
    assert set(lab) <= sft_data.LABEL_ROW_KEYS and set(lab["soft_parameters"] or {}) <= sft_data.SOFT_PARAMETER_KEYS
    if label[0] == "audit":
        assert lab["soft_parameters"]["k_label"] == label[1]
    value, status = B._evaluation(ev, row, B.T0_EVALUATION_SEEDS)
    assert status == evaluation[0] and (value is None) == (status == "divergent")
    assert ev.get("divergent_seeds") == evaluation[1]
    if cand == [0.9] * 10:                                              # D4 A's rows, key for key
        d4a_lab, d4a_ev = audit.evidence_blocks("unused", [{**res[0], "candidate_metrics": cand}])
        assert set(lab) == set(d4a_lab[0]) and set(ev) == set(d4a_ev[0])
    counts = X.counts(labels, evaluations)
    assert sum(counts["labels"].values()) == 1 and sum(counts["evaluations"].values()) == 1
    assert counts["evaluations"][evaluation[0]] == 1 and counts["action_target_rule"].startswith("u = -g")


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
    ("contingency", "itself a contingency audit"),
    ("path", "must be results/r1/evidence"),
    ("outside", "inside the paper root"),
])
def test_contingency_needs_a_sweep2_seed_run_stop(tmp_path, monkeypatch, kind, match):
    paper = tmp_path / "paper"
    stopped = _stopped(paper, reason="audit deadline exceeded" if kind == "reason" else STOP_REASON,
                       source="sweep1" if kind == "source" else "sweep2", completed=kind == "completed",
                       contingency=kind == "contingency")
    stop_sha = _sha((stopped / "STOP.json").read_bytes())
    monkeypatch.setattr(audit, "_published_bytes", lambda root, rel: _plan_text(stop_sha).encode())
    rel = {"path": Path("results/r1/other/x"), "outside": tmp_path / "elsewhere/results/r1/evidence/C3_audit_EVIDENCE_x"
           }.get(kind, stopped.relative_to(paper))
    with pytest.raises(ValueError, match=match):
        X.check_contingency(paper, rel)


def test_contingency_refuses_a_symlinked_stopped_audit(tmp_path, monkeypatch):
    """A relative or absolute path through a symlinked C3_audit_EVIDENCE_* directory is refused (as the evidence output
    path is); the absolute spelling of the real directory is accepted."""
    paper = tmp_path / "paper"
    stopped = _stopped(paper)
    stop_sha = _sha((stopped / "STOP.json").read_bytes())
    monkeypatch.setattr(audit, "_published_bytes", lambda root, rel: _plan_text(stop_sha).encode())
    outside = tmp_path / "outside"
    shutil.copytree(stopped, outside)
    link = paper / "results/r1/evidence/C3_audit_EVIDENCE_link"
    link.symlink_to(outside)
    for given in (link.relative_to(paper), link):
        with pytest.raises(ValueError, match="symlink component"):
            X.check_contingency(paper, given)
    assert X.check_contingency(paper, stopped)["stopped_audit"] == str(stopped.relative_to(paper))


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
                if isinstance(m, dict):            # a failed run, as run_config records it under the contingency
                    out.append({"seed": s, "success": False, "changed_files": False, "metric": None,
                                "wall_seconds": 1.0, "worker_runtime": runtime, **m})
                    continue
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
    assert label["label_kind"] == "audit" and label["soft_parameters"]["k_label"] == 4
    assert math.isclose(label["delta_label"], 0.1) and set(label) == {"proposal_id", "node", "label_kind", "seeds",
                                                                       "delta_label", "se_label", "soft_parameters"}
    evaluation = json.loads((out / "evaluation_block.jsonl").read_text().splitlines()[0])
    assert "divergent_seeds" not in evaluation and "k_evaluation" not in evaluation    # complete: D4 A's row
    completion = json.loads((out / "evidence_completion.json").read_text())
    assert completion["schema"] == X.D4B_COMPLETION_SCHEMA
    assert completion["d4b_contingency"]["stop_sha256"] == stop_sha
    assert completion["d4b_contingency"]["counts"] == {
        "labels": {"divergent": 0, "partial": 1, "complete": 0, "rule_noop": 0},
        "evaluations": {"divergent": 0, "partial": 0, "complete": 1}, "action_target_rule": X.ACTION_TARGET_RULE}
    env = json.loads((out / "environment.json").read_text())
    assert env["d4b_contingency"]["row"] == X.D4B_ROW
    assert (out / X.STOP_COPY).read_bytes() == (stopped / "STOP.json").read_bytes()    # bound inside the audit


def test_contingency_reads_an_exit_1_non_finite_failure_as_divergence(tmp_path, monkeypatch):
    stopped = _stopped(tmp_path)
    stop_sha = _sha((stopped / "STOP.json").read_bytes())
    monkeypatch.setattr(audit, "_published_bytes", lambda root, rel: _plan_text(stop_sha).encode())

    def metric(key, seed):
        if key == "c" and seed in (7006, 7009):
            return {"failure": "exit code 1", "failure_category": "runtime_error", "log_tail": NAN_TAIL}
        return 0.8 + (0.1 if key == "c" else 0)
    out, _ = _world(tmp_path, monkeypatch, metric, d4b=stopped.relative_to(tmp_path))
    evaluation = json.loads((out / "evaluation_block.jsonl").read_text().splitlines()[0])
    assert evaluation["divergent_seeds"] == [7006, 7009] and evaluation["k_evaluation"] == 3
    assert math.isclose(evaluation["delta_evaluation"], 0.1)
    counts = json.loads((out / "evidence_completion.json").read_text())["d4b_contingency"]["counts"]
    assert counts["evaluations"] == {"divergent": 0, "partial": 1, "complete": 0}


@pytest.mark.parametrize("failure", [
    {"failure": "exit code 137", "log_tail": "Killed"},                                    # an OOM kill
    {"failure": "exit code 2", "failure_category": "invalid_config", "log_tail": "nan"},   # a config rejection
    {"failure": "exit code 1", "failure_category": "runtime_error", "log_tail": "KeyError: 'col'"},
])
def test_contingency_still_stops_on_other_failures(tmp_path, monkeypatch, failure):
    stopped = _stopped(tmp_path)
    stop_sha = _sha((stopped / "STOP.json").read_bytes())
    monkeypatch.setattr(audit, "_published_bytes", lambda root, rel: _plan_text(stop_sha).encode())
    with pytest.raises(ValueError, match="invalid audit result for n/c"):
        _world(tmp_path, monkeypatch, lambda k, s: failure if (k, s) == ("c", 7003) else 0.8,
               d4b=stopped.relative_to(tmp_path))
    out = tmp_path / "results/r1/evidence/C3_audit_EVIDENCE_new"
    assert (out / "STOP.json").is_file() and not (out / "evidence_completion.json").exists()


def test_contingency_stops_on_an_incumbent_divergence(tmp_path, monkeypatch):
    stopped = _stopped(tmp_path)
    stop_sha = _sha((stopped / "STOP.json").read_bytes())
    monkeypatch.setattr(audit, "_published_bytes", lambda root, rel: _plan_text(stop_sha).encode())
    with pytest.raises(ValueError, match="incumbent diverged.*STOP"):
        _world(tmp_path, monkeypatch, lambda k, s: float("nan") if (k, s) == ("i", 7004) else 0.8,
               d4b=stopped.relative_to(tmp_path))
    out = tmp_path / "results/r1/evidence/C3_audit_EVIDENCE_new"
    assert json.loads((out / "STOP.json").read_text())["reason"].startswith("D4B blocks: D4B: the incumbent diverged")
    assert not (out / "label_block.jsonl").exists()


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
    completion = json.loads((out / "evidence_completion.json").read_text())
    assert completion["d4b_contingency"]["counts"]["labels"]["divergent"] == 1
    assert completion["d4b_contingency"]["counts"]["action_target_rule"].startswith("u = -g")


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


# ------------------------------------------------------------------------------------------------- verification
def _verify_world(tmp_path, monkeypatch):
    """A synthetic contingency audit directory that ``verify_evidence_completion(source='sweep2')`` accepts (built on
    test_c3_sweep2_audit's end-to-end round trip): candidate seed 7002 diverged (exit 1, NaN in its log)."""
    from r1.c3 import release
    from r1.tests.test_c3_evidence_guards import FAKE_ENV, fake_basis, sha
    monkeypatch.setattr(release, "require_integrity_or_test_release", lambda *a: None)
    stopped = _stopped(tmp_path)
    stop_sha = sha(stopped / "STOP.json")
    plan_md = {"t": _plan_text(stop_sha)}
    monkeypatch.setattr(audit, "_published_bytes", lambda root, rel: plan_md["t"].encode())
    table = tmp_path / "table"
    table.mkdir()
    for name in ("build.json", "proposals.jsonl", "configs.json"):
        (table / name).write_text("{}")
    monkeypatch.setattr(D, "load_table", lambda _: [{"proposal_id": "x", "node": "n", "noop": False,
                                                    "duplicate": False, "sigma_node": 0.5}])
    auth = tmp_path / SB.AUTHORIZATION["path"]
    auth.parent.mkdir(parents=True, exist_ok=True)
    auth.write_text("a")
    addendum = auth.parent / "c3_sweep2_b2_addendum_x.md"
    addendum.write_text("addendum")
    index = tmp_path / "index"
    index.write_text("index")
    plan = [{"proposal_id": "x", "node": "n", "candidate_hash": "c", "incumbent_hash": "i",
             "reason": "full_population", "inclusion_probability": 1.0}]
    binding = {"counts": {"eligible": 1, "noops": 0, "duplicates": 0}, "source": "sweep2", "extract_sha256": "e" * 64}
    monkeypatch.setattr(audit, "evidence_plan", lambda *a: (plan, binding))
    out = tmp_path / "results/r1/evidence/C3_audit_EVIDENCE_new"
    out.mkdir()
    (out / "plan.jsonl").write_text("".join(json.dumps(x) + "\n" for x in plan))
    runtime = {"worker_python": FAKE_ENV["worker_python"], "prefix": FAKE_ENV["worker_prefix"],
               "base_prefix": "/base", "versions": FAKE_ENV["worker_versions"],
               "package_list_sha256": FAKE_ENV["package_list_sha256"], "worker_command_python": "/wrapper/python3",
               "worker_python_realpath": "/system/python3"}
    rows = []
    for h in ("c", "i"):
        for s in audit.DEFAULT_SEEDS:
            div = h == "c" and s == 7002
            rows.append({"node": "n", "config_hash": h, "seed": s, "success": not div, "changed_files": False,
                         "failure": "exit code 1" if div else None,
                         "metric": None if div else 0.8 + (0.1 if h == "c" else 0) + (s - 7001) * 1e-3,
                         "wall_seconds": 1, "worker_runtime": runtime,
                         **({"failure_category": "runtime_error", "log_tail": NAN_TAIL} if div else {})})
    audit.RunCache(out / "runs.jsonl").add(rows)
    d4b = X.check_contingency(tmp_path, stopped.relative_to(tmp_path))
    (out / X.STOP_COPY).write_bytes(X.stopped_bytes(tmp_path, d4b))
    res = X.validate_results(plan, audit.evidence_cache(plan, out / "runs.jsonl"), audit.DEFAULT_SEEDS)
    labels, evaluations = X.blocks(table, res)
    (out / "label_block.jsonl").write_text("".join(json.dumps(x) + "\n" for x in labels))
    (out / "evaluation_block.jsonl").write_text("".join(json.dumps(x) + "\n" for x in evaluations))
    pins = {"sweep2_index_sha256": sha(index), "sweep2_extract_sha256": "e" * 64,
            "table_proposals_sha256": sha(table / "proposals.jsonl"), "table_configs_sha256": sha(table / "configs.json")}
    env = {"harness_commit": audit.AUDIT_HARNESS, "harness_dirty": False, "scikit_learn": "1.8.0", "python": "3.13.2",
           "uv_lock_sha256": "locked", "paper_code_clean": True, "paper_code_commit": "a" * 40,
           "review_path": "docs/r1/reviews/test.md", "environment_basis": fake_basis("3.13.2"),
           "environment_checks_at_start": {k: fake_basis("3.13.2")["interpreter"][k] for k in
                                           ("build", "prefix", "wrapper_target", "package_list_sha256",
                                            "newest_dist_info_mtime_utc")},
           "harness_untracked": {"data_caches_sha256": fake_basis()["data_caches_sha256"]},
           "worker_runtime_basis": audit.worker_runtime_basis(),
           "b2_addendum": {"path": "docs/r1/authorizations/c3_sweep2_b2_addendum_x.md", "sha256": sha(addendum),
                           "pins": pins},
           "source": "sweep2", "sweep2_harness_equivalence": {"diff": "empty", "paths": list(audit.SWEEP2_EQUAL_PATHS)},
           **FAKE_ENV}
    env.pop("harness_root", None)
    monkeypatch.setattr(audit, "replay_environment_basis", lambda *a: fake_basis("3.13.2"))
    monkeypatch.setattr(audit, "b2_addendum", lambda *a: dict(env["b2_addendum"]))
    review = b"Code-Commit: " + b"a" * 40 + b"\nVerdict: ACCEPTED\n"
    env["review_sha256"] = hashlib.sha256(review).hexdigest()
    monkeypatch.setattr(audit.subprocess, "check_output",
                        lambda cmd, **kw: "published\n" if "rev-parse" in cmd else review)
    monkeypatch.setattr(audit.subprocess, "run", lambda *a, **kw: None)
    (out / "resources.json").write_text("{}")

    def write(env_d4b=True, comp_d4b=True):
        e = dict(env)
        if env_d4b:
            e["d4b_contingency"] = d4b
        (out / "environment.json").write_text(json.dumps(e))
        c = audit._completion("sweep2", paper_root=tmp_path, table=table, out=out, index=index, classification=None,
                              binding=binding, addendum_sha256=sha(addendum), label_block=out / "label_block.jsonl",
                              d4b={**d4b, "counts": X.counts(labels, evaluations)} if comp_d4b else None)
        (out / "evidence_completion.json").write_text(json.dumps(c, indent=2) + "\n")

    def verify():
        return audit.verify_evidence_completion(table, out / "label_block.jsonl", tmp_path, index, None, "sweep2")
    return {"write": write, "verify": verify, "plan_md": plan_md, "stopped": stopped, "out": out, "labels": labels,
            "table": table, "index": index, "stop_sha": stop_sha}


def test_verify_re_derives_a_contingency_audit(tmp_path, monkeypatch):
    w = _verify_world(tmp_path, monkeypatch)
    w["write"]()
    got = w["verify"]()
    assert got["schema"] == X.D4B_COMPLETION_SCHEMA and got["d4b_contingency"]["counts"]["labels"]["partial"] == 1
    assert w["labels"][0]["soft_parameters"]["k_label"] == 4
    # the stopped directory may be archived later: the STOP copy inside the audit carries the binding
    shutil.move(str(w["stopped"]), str(tmp_path / "archived_stopped_audit"))
    assert w["verify"]()["schema"] == X.D4B_COMPLETION_SCHEMA


@pytest.mark.parametrize("case,match", [
    ("completion_only", "outside a sweep-2 contingency audit"),
    ("environment_only", "evidence completion metadata mismatch"),
    ("row_withdrawn", "D4B is OFF"),
    ("row_text_changed", "no longer matches its author row"),
    ("stop_copy_changed", "D4B is OFF"),
    ("stop_copy_missing", "lacks its d4b_stopped_STOP.json"),
    ("record_changed", "evidence completion metadata mismatch"),       # the path is informational after the run
    ("stop_sha_changed", "no longer matches its author row"),
    ("runs_changed", "neither valid nor divergent"),
])
def test_verify_refuses_a_contingency_audit_that_no_longer_holds(tmp_path, monkeypatch, case, match):
    w = _verify_world(tmp_path, monkeypatch)
    w["write"](env_d4b=case != "completion_only", comp_d4b=case != "environment_only")
    out = w["out"]
    if case == "row_withdrawn":
        w["plan_md"]["t"] = _plan_text(None)
    elif case == "row_text_changed":
        w["plan_md"]["t"] = _plan_text(w["stop_sha"]).replace("uses", "applies")
    elif case == "stop_copy_changed":
        (out / X.STOP_COPY).write_text(json.dumps({"label": "EVIDENCE", "reason": STOP_REASON, "unscheduled": 4}))
    elif case == "stop_copy_missing":
        (out / X.STOP_COPY).rename(out / "moved")
    elif case == "record_changed":
        env = json.loads((out / "environment.json").read_text())
        env["d4b_contingency"]["stopped_audit"] = "results/r1/evidence/C3_audit_EVIDENCE_other"
        (out / "environment.json").write_text(json.dumps(env))
    elif case == "stop_sha_changed":
        env = json.loads((out / "environment.json").read_text())
        env["d4b_contingency"]["stop_sha256"] = "0" * 64
        (out / "environment.json").write_text(json.dumps(env))
    elif case == "runs_changed":                     # the divergent run re-labelled as an OOM kill
        lines = (out / "runs.jsonl").read_text().splitlines()
        lines = [x.replace('"exit code 1"', '"exit code 137"') for x in lines]
        (out / "runs.jsonl").write_text("\n".join(lines) + "\n")
    with pytest.raises(ValueError, match=match):
        w["verify"]()


def test_release_check_refuses_a_contingency_audit_with_the_real_verifier(tmp_path, monkeypatch):
    """Not mocked: verify_evidence_completion passes on the contingency audit, then the sweep-2 release check refuses
    its /5 schema."""
    from r1.c3 import release_checks
    w = _verify_world(tmp_path, monkeypatch)
    w["write"]()
    monkeypatch.setattr(release_checks, "_sweep2_batch_published", lambda: None)
    with pytest.raises(ValueError, match="not a sweep-2 audit completion"):
        release_checks.sweep2_integrity(w["table"], w["out"], paper_root=tmp_path, index=w["index"])


def test_sft_reader_refuses_a_contingency_completion(tmp_path, monkeypatch):
    """sft_data.LabelBlockSource refuses a /5 completion by name, even for a block of rule no-ops whose rows it could
    otherwise read."""
    from r1.c3 import release
    from r1.c3.train import sft_data
    monkeypatch.setattr(release, "require_integrity_or_test_release", lambda *a: None)
    audit_dir = tmp_path / "results/r1/evidence/C3_audit_EVIDENCE_new"
    audit_dir.mkdir(parents=True)
    block = audit_dir / "label_block.jsonl"
    block.write_text(json.dumps({"proposal_id": "p", "node": "n", "label_kind": "rule_noop", "delta_label": 0.0,
                                 "se_label": 0.0, "soft_parameters": {"inert": True}}) + "\n")
    for completion in ({"schema": X.D4B_COMPLETION_SCHEMA},
                       {"schema": audit.SWEEP2_COMPLETION_SCHEMA, "d4b_contingency": {"row": X.D4B_ROW}}):
        (audit_dir / "evidence_completion.json").write_text(json.dumps({
            **completion, "label_seeds": list(sft_data.LABEL_SEEDS), "index_sha256": "x" * 64,
            "label_block_sha256": _sha(block.read_bytes())}))
        with pytest.raises(sft_data.SFTDataError, match="D4B contingency"):
            sft_data.LabelBlockSource(block)._load()


def test_cli_passes_the_contingency_flag_only_when_given(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(audit, "evidence_run", lambda *a, **kw: seen.append(kw["d4b_after_stop"]) or {})
    base = ["evidence-run", "--table", "t", "--paper-root", "p", "--index", "i", "--source", "sweep2", "--out", "o",
            "--workers", "1", "--deadline", "10", "--code-commit", "c", "--code-review", "r", "--addendum", "a",
            "--scratch-root", "/tmp/s", "--required-scratch-bytes", "1", "--ceph-reserve-files", "1"]
    assert audit.main(base) == 0
    assert audit.main(base + ["--d4b-after-stop", "results/r1/evidence/C3_audit_EVIDENCE_x"]) == 0
    assert seen == [None, Path("results/r1/evidence/C3_audit_EVIDENCE_x")]
