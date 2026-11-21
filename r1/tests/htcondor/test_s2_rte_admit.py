"""Tests for the R1-SWEEP2-RTE-DIAG collection admission (six diagnosed runtime-error trials)."""
import hashlib
import json
from pathlib import Path

import pytest

from sweep2 import s2_c2_lib as lib


def _write_artifact(sealed, rel, data):
    path = sealed / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode())
    with (sealed / "SHA256SUMS").open("a") as fh:
        fh.write(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {rel}\n")


def _sealed(tmp_path, *, trials=(("node__s1", "node__s1-trial-005", "ParserError"),)):
    sealed = tmp_path / "chunk"
    sealed.mkdir()
    worker = {"trials": 20, "successful": 17, "successful_with_metrics": 17, "failures": 3,
              "runtime_errors": len(trials), "skipped": 0,
              "failures_by_category": {"invalid_config": 3 - len(trials), "runtime_error": len(trials)},
              "roots": {campaign: {"trials": 20, "successful": 17, "successful_with_metrics": 17}
                        for campaign, _, _ in trials}}
    checks = {"node": "digits_mlp", "memory_mode": "append_only_summary", "expected_roots": 18, "roots": 18,
              "root_failures": 0, "llm_calls": 100, "parse_failures": 0, "worker": worker}
    _write_artifact(sealed, "out/collection_checks.json", json.dumps(checks))
    _write_artifact(sealed, "out/worker_failure.json", json.dumps(worker))
    for campaign, trial_id, exception in trials:
        index = int(trial_id.rsplit("-", 1)[-1])
        rows = [{"trial_id": trial_id, "budget_index": index, "failure_category": "runtime_error"},
                {"trial_id": f"{campaign}-trial-001", "budget_index": 1, "failure_category": "kept"}]
        _write_artifact(sealed, f"work/roots/{campaign}/root_trials.jsonl",
                        "\n".join(json.dumps(row) for row in rows) + "\n")
        _write_artifact(sealed, f"work/roots/{campaign}/art/trial-{index:03d}/run.log",
                        f"STATUS=failed\nFAILURE_CATEGORY=runtime_error\nFAILURE_MESSAGE={exception}: bad value\n")
    record = {"chunk_id": "digits_mlp-append_only_summary", "stop": "STOP: 1 worker runtime_error(s)",
              "finished_utc": "x", "label": "EVIDENCE"}
    digest = hashlib.sha256(b"record").hexdigest()
    return sealed, record, digest


def test_admits_declared_trial_and_counts_it_as_invalid_config(tmp_path, monkeypatch):
    sealed, record, digest = _sealed(tmp_path)
    monkeypatch.setitem(lib.RTE_DIAGNOSED, "digits_mlp-append_only_summary", {
        "record_sha256": digest, "stop": record["stop"],
        "trials": [("node__s1", "node__s1-trial-005", "ParserError")]})
    gates, admitted, key = lib._admitted_diagnosed_chunk(record, digest, sealed)
    assert key == ("digits_mlp", "append_only_summary")
    assert gates["worker"]["runtime_errors"] == 0
    assert gates["worker"]["failures_by_category"] == {"invalid_config": 3}
    assert gates["worker"]["admitted_diagnosed_runtime_errors"] == 1
    assert admitted[0]["trial_id"] == "node__s1-trial-005"


@pytest.mark.parametrize("mutate", ["digest", "trial", "exception", "artifact_hash", "node_mismatch"])
def test_rejects_anything_outside_the_declared_record(tmp_path, monkeypatch, mutate):
    sealed, record, digest = _sealed(tmp_path)
    entry = {"record_sha256": digest, "stop": record["stop"],
             "trials": [("node__s1", "node__s1-trial-005", "ParserError")]}
    if mutate == "digest":
        entry["record_sha256"] = "0" * 64
    elif mutate == "trial":
        entry["trials"] = [("node__s1", "node__s1-trial-004", "ParserError")]
    elif mutate == "exception":
        entry["trials"] = [("node__s1", "node__s1-trial-005", "TypeError")]
    elif mutate == "artifact_hash":
        (sealed / "out/collection_checks.json").write_text("{}")
    elif mutate == "node_mismatch":
        record["chunk_id"] = "other-node-append_only_summary"
    monkeypatch.setitem(lib.RTE_DIAGNOSED, "digits_mlp-append_only_summary", entry)
    with pytest.raises(lib.Stop):
        lib._admitted_diagnosed_chunk(record, digest, sealed)
