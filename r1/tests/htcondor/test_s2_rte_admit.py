"""Tests for the R1-SWEEP2-RTE-DIAG collection admission (six diagnosed runtime-error trials)."""
import hashlib
import json
from pathlib import Path

import pytest

from sweep2 import s2_c2_lib as lib


def _sealed(tmp_path):
    sealed = tmp_path / "chunk"
    (sealed / "out").mkdir(parents=True)
    worker = {"trials": 20, "successful": 17, "successful_with_metrics": 17, "failures": 3,
              "runtime_errors": 1, "skipped": 0,
              "failures_by_category": {"invalid_config": 2, "runtime_error": 1},
              "roots": {"node__s1": {"trials": 20, "successful": 17, "successful_with_metrics": 17}}}
    checks = {"expected_roots": 18, "roots": 18, "root_failures": 0, "llm_calls": 100,
              "parse_failures": 0, "worker": worker}
    failure = dict(worker)
    (sealed / "out" / "collection_checks.json").write_text(json.dumps(checks))
    (sealed / "out" / "worker_failure.json").write_text(json.dumps(failure))
    root = sealed / "work" / "roots" / "node__s1"
    (root / "art" / "trial-005").mkdir(parents=True)
    (root / "root_trials.jsonl").write_text(json.dumps(
        {"trial_id": "node__s1-trial-005", "budget_index": 5, "failure_category": "runtime_error"}) + "\n")
    (root / "art" / "trial-005" / "run.log").write_text(
        "STATUS=failed\nFAILURE_CATEGORY=runtime_error\nFAILURE_MESSAGE=ParserError: bad yaml\n")
    record = {"chunk_id": "node-mode", "stop": "STOP: 1 worker runtime_error(s)", "finished_utc": "x",
              "label": "EVIDENCE"}
    digest = hashlib.sha256(b"record").hexdigest()
    return sealed, record, digest


def test_admits_only_declared_trial_and_counts_it_as_invalid_config(tmp_path, monkeypatch):
    sealed, record, digest = _sealed(tmp_path)
    monkeypatch.setitem(lib.RTE_DIAGNOSED, "node-mode", {
        "record_sha256": digest, "stop": record["stop"],
        "trials": [("node__s1", "node__s1-trial-005", "ParserError")]})
    gates, admitted = lib._admitted_diagnosed_chunk(record, digest, sealed)
    assert gates["worker"]["runtime_errors"] == 0
    assert gates["worker"]["failures_by_category"] == {"invalid_config": 3}
    assert gates["worker"]["admitted_diagnosed_runtime_errors"] == 1
    assert admitted[0]["trial_id"] == "node__s1-trial-005"


@pytest.mark.parametrize("mutate", ["digest", "trial", "exception"])
def test_rejects_anything_outside_the_declared_record(tmp_path, monkeypatch, mutate):
    sealed, record, digest = _sealed(tmp_path)
    entry = {"record_sha256": digest, "stop": record["stop"],
             "trials": [("node__s1", "node__s1-trial-005", "ParserError")]}
    if mutate == "digest":
        entry["record_sha256"] = "0" * 64
    elif mutate == "trial":
        entry["trials"] = [("node__s1", "node__s1-trial-004", "ParserError")]
    else:
        entry["trials"] = [("node__s1", "node__s1-trial-005", "TypeError")]
    monkeypatch.setitem(lib.RTE_DIAGNOSED, "node-mode", entry)
    with pytest.raises(lib.Stop):
        lib._admitted_diagnosed_chunk(record, digest, sealed)
