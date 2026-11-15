"""W2-3 check: every ledger made exactly W worker runs (``r1/scripts/w2_runs_total_check.py``)."""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from r1.scripts import w2_runs_total_check as C
from r1.scripts.w2_execute_all_identity_check import main as identity_main

W = 20


def ledger(tmp: Path, name: str, worker_rows: int, precheck_rows: int = 0, skip_rows: int = 0, gz: bool = False) -> Path:
    """Rows in trial order: prechecks and control-plane skips first, then worker runs."""
    rows = []
    for _ in range(precheck_rows):
        rows.append({"decision": "failed_invalid", "worker_mode": "local_precheck", "extra": {}})
    for _ in range(skip_rows):
        rows.append({"decision": "skipped", "worker_mode": "control_plane", "extra": {"control": {"action": "skip"}}})
    for _ in range(worker_rows):
        rows.append({"decision": "kept", "worker_mode": "local", "extra": {}})
    for b, r in enumerate(rows, 1):
        r["budget_index"] = b
    d = tmp / name
    d.mkdir(parents=True)
    text = "".join(json.dumps(r) + "\n" for r in rows)
    if gz:
        p = d / "root_trials.jsonl.gz"
        p.write_bytes(gzip.compress(text.encode()))
    else:
        p = d / "root_trials.jsonl"
        p.write_text(text)
    return p


def summary(tmp: Path, paths, capsys) -> Path:
    identity_main([str(p) for p in paths] + ["--runs-total", str(W)])
    out = capsys.readouterr().out
    s = tmp / "identity_check.json"
    s.write_text(out)
    return s


def run(argv, capsys):
    code = C.main(argv)
    return code, json.loads(capsys.readouterr().out)


def test_pass_on_recomputed_ledgers_including_prechecks(tmp_path, capsys):
    a = ledger(tmp_path, "a", 20)
    b = ledger(tmp_path, "b", 20, precheck_rows=3, gz=True)       # 23 trials, still 20 runs
    code, out = run([str(a), str(b), "--runs-total", "20"], capsys)
    assert code == 0 and out["status"] == "PASS" and out["ledgers"] == 2


def test_pass_from_identity_check_summary(tmp_path, capsys):
    paths = [ledger(tmp_path, f"l{i}", 20, precheck_rows=i % 2) for i in range(4)]
    s = summary(tmp_path, paths, capsys)
    code, out = run(["--summary", str(s), "--runs-total", "20"], capsys)
    assert code == 0 and out["ledgers"] == 4


def test_stop_kinds(tmp_path, capsys):
    cap = ledger(tmp_path, "cap", 19, precheck_rows=21)           # 40 trials, 19 runs: stopped by the trial cap
    early = ledger(tmp_path, "early", 15)                          # ended before either cap
    ok = ledger(tmp_path, "ok", 20, skip_rows=2)
    code, out = run([str(cap), str(early), str(ok), "--runs-total", "20"], capsys)
    assert code == 3 and out["status"] == "STOP" and out["ledgers_differing"] == 2
    assert out["by_kind"] == {"short_at_trial_cap": 1, "short_before_trial_cap": 1}
    kinds = {Path(d["ledger"]).parent.name: d["kind"] for d in out["differing"]}
    assert kinds == {"cap": "short_at_trial_cap", "early": "short_before_trial_cap"}


def test_over_cap_from_summary(tmp_path, capsys):
    s = tmp_path / "s.json"
    s.write_text(json.dumps({"status": "IDENTICAL", "ledgers": 1, "results": [
        {"ledger": "x/root_trials.jsonl", "rows": 21, "runs_total": 20, "worker_runs_total": 21}]}))
    code, out = run(["--summary", str(s), "--runs-total", "20"], capsys)
    assert code == 3 and out["by_kind"] == {"over_cap": 1}


@pytest.mark.parametrize("data,msg", [
    ({"status": "OTHER", "ledgers": 0, "results": []}, "not a w2_execute_all_identity_check summary"),
    ({"status": "IDENTICAL", "ledgers": 2, "results": [{"ledger": "a", "rows": 20, "runs_total": 20, "worker_runs_total": 20}]},
     "ledger count differs"),
    ({"status": "IDENTICAL", "ledgers": 1, "results": [{"ledger": "a", "rows": 20, "runs_total": 10, "worker_runs_total": 10}]},
     "made with runs_total 10"),
    ({"status": "IDENTICAL", "ledgers": 1, "results": [{"ledger": "a", "rows": 20, "runs_total": 20, "worker_runs_total": "20"}]},
     "is not an integer"),
    ({"status": "IDENTICAL", "ledgers": 2, "results": [{"ledger": "a", "rows": 20, "runs_total": 20, "worker_runs_total": 20},
                                                      {"ledger": "a", "rows": 20, "runs_total": 20, "worker_runs_total": 20}]},
     "more than once"),
])
def test_bad_summaries(tmp_path, capsys, data, msg):
    s = tmp_path / "s.json"
    s.write_text(json.dumps(data))
    code, out = run(["--summary", str(s), "--runs-total", "20"], capsys)
    assert code == 2 and out["status"] == "BAD_INPUT" and msg in out["error"]


def test_refuses_sealed_and_wrong_names(tmp_path, capsys):
    sealed = ledger(tmp_path / "r1_sealed", "x", 20)
    code, out = run([str(sealed), "--runs-total", "20"], capsys)
    assert code == 2 and "r1_sealed" in out["error"]
    other = tmp_path / "trials.jsonl"
    other.write_text("")
    code, out = run([str(other), "--runs-total", "20"], capsys)
    assert code == 2 and "not a root_trials.jsonl" in out["error"]
    code, out = run(["--runs-total", "20"], capsys)
    assert code == 2


def test_summary_and_ledgers_together_detect_duplicates(tmp_path, capsys):
    a = ledger(tmp_path, "a", 20)
    s = summary(tmp_path, [a], capsys)
    code, out = run(["--summary", str(s), str(a), "--runs-total", "20"], capsys)
    assert code == 2 and "more than once" in out["error"]
