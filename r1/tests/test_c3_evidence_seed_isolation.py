"""Evidence-only label/evaluation isolation; no production data is used."""
import json

import numpy as np
import pytest

from r1.c3 import offline_eval as oe
from r1.c3 import analysis_guard


@pytest.fixture(autouse=True)
def _after_test_release(monkeypatch):
    """These tests exercise the raw-block readers as they behave once the T0 test release row exists (PRE-STAGE A);
    the lock itself is tested in test_c3_release.py."""
    from r1.c3 import release
    monkeypatch.setattr(release, "test_released", lambda *a, **k: True)


def _fixture(tmp_path, monkeypatch, evaluation_value=1.0):
    # This synthetic fixture isolates seed handling; gate behavior has its own tests.
    monkeypatch.setattr(analysis_guard, "guard_table", lambda *_: None)
    (tmp_path / "build.json").write_text(json.dumps({"label": "EVIDENCE"}))
    monkeypatch.setattr(oe, "_verify_evidence_inputs", lambda *_: None)
    row = {"proposal_id": "p", "source": "s", "node": "n", "instance_seed": 1,
           "noop": False, "duplicate": False, "sigma_node": 1.0,
           "features": {"active_equals_incumbent": False, "active_seen_before": False}}
    monkeypatch.setattr(oe, "load_table", lambda _: [row])
    audit = {"proposal_id": "p", "reason": ["random"], "seeds": list(range(7001, 7011)),
             "candidate_metrics": [0.2] * 5 + [evaluation_value] * 5,
             "incumbent_metrics": [0.0] * 10, "delta_audit": evaluation_value,
             "se": evaluation_value}
    (tmp_path / "audits.jsonl").write_text(json.dumps(audit) + "\n")
    return audit


def test_evidence_label_uses_only_label_seed_statistics(tmp_path, monkeypatch):
    audit = _fixture(tmp_path, monkeypatch, 1.0)
    first = oe.assemble(tmp_path)[0]
    audit["candidate_metrics"][5:] = [99.0] * 5
    audit["delta_audit"] = audit["se"] = 99.0
    (tmp_path / "audits.jsonl").write_text(json.dumps(audit) + "\n")
    second = oe.assemble(tmp_path)[0]
    assert np.allclose(first["soft"], second["soft"])
    assert first["label_delta_audit"] == second["label_delta_audit"] == 0.2
    assert first["label_se_audit"] == second["label_se_audit"] == 0.0
    assert "delta_audit_all" not in first and "se_audit" not in first
    assert first["weight"] == second["weight"]
    assert first["delta_true"] == 1.0 and second["delta_true"] == 99.0


def test_evidence_rejects_unsplit_or_misordered_or_incomplete_seeds(tmp_path, monkeypatch):
    audit = _fixture(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="seed split"):
        oe.assemble(tmp_path, seed_split=False)
    audit["seeds"] = list(reversed(audit["seeds"]))
    (tmp_path / "audits.jsonl").write_text(json.dumps(audit) + "\n")
    with pytest.raises(ValueError, match="ordered seeds"):
        oe.assemble(tmp_path)
    audit["seeds"] = list(range(7001, 7011))
    audit["candidate_metrics"][-1] = None
    (tmp_path / "audits.jsonl").write_text(json.dumps(audit) + "\n")
    with pytest.raises(ValueError, match="invalid candidate_metrics"):
        oe.assemble(tmp_path)


def test_pilot_remains_able_to_run_unsplit_sensitivity(tmp_path, monkeypatch):
    _fixture(tmp_path, monkeypatch)
    (tmp_path / "build.json").write_text(json.dumps({"label": "PILOT"}))
    row = oe.assemble(tmp_path, seed_split=False)[0]
    assert row["delta_true"] == 1.0 and row["delta_audit_all"] == 1.0


def test_classification_cannot_be_claimed_on_non_evidence_table(tmp_path, monkeypatch):
    _fixture(tmp_path, monkeypatch)
    (tmp_path / "build.json").write_text(json.dumps({"label": "PILOT", "classification": {"path": "x"}}))
    with pytest.raises(ValueError, match="must carry an EVIDENCE label"):
        oe.assemble(tmp_path)


def test_evidence_consumer_fails_closed_when_verifier_rejects(tmp_path, monkeypatch):
    _fixture(tmp_path, monkeypatch)
    def reject(*_):
        raise ValueError("completion missing or corrupt")
    monkeypatch.setattr(oe, "_verify_evidence_inputs", reject)
    with pytest.raises(ValueError, match="completion missing or corrupt"):
        oe.assemble(tmp_path)


def test_evidence_consumer_uses_completion_verifier(tmp_path, monkeypatch):
    from r1.c3 import audit
    from r1 import harness
    table = tmp_path / "table"
    table.mkdir()
    index = tmp_path / "index.json"
    sidecar = tmp_path / "sidecar.json"
    audits = tmp_path / "audits" / "audits.jsonl"
    metadata = {"label": "EVIDENCE", "classification": {"path": str(sidecar)},
                "sweep_index": {"path": str(index)}}
    seen = []
    monkeypatch.setattr(audit, "verify_evidence_completion", lambda *args: seen.append(args))
    monkeypatch.setattr(harness, "REPO", tmp_path)
    oe._verify_evidence_inputs(table, audits, metadata)
    assert seen == [(table, audits, tmp_path, index, sidecar)]


def test_evidence_missing_completion_cannot_be_consumed(tmp_path, monkeypatch):
    from r1 import harness
    monkeypatch.setattr(analysis_guard, "guard_table", lambda *_: None)
    from r1.c3 import audit as audit_module
    table = tmp_path / "table"
    table.mkdir()
    (table / "build.json").write_text(json.dumps({"label": "EVIDENCE",
        "classification": {"path": str(tmp_path / "sidecar.json")},
        "sweep_index": {"path": str(tmp_path / "index.json")}}))
    monkeypatch.setattr(harness, "REPO", tmp_path)
    # e2 (R1-B2-GO B4 (a)) removed the task-native attestation STOP; the missing completion record still
    # cannot be consumed. A legacy mixed audits.jsonl path is refused outright (007a8d1c: EVIDENCE consumes
    # label_block.jsonl only).
    with pytest.raises(ValueError, match="unexpected label block path"):
        oe.assemble(table, tmp_path / "audit" / "audits.jsonl")
    # The split label block without its completion record cannot be consumed either.
    with pytest.raises(FileNotFoundError, match="evidence_completion.json"):
        oe.assemble(table, tmp_path / "audit" / "label_block.jsonl")


def test_evidence_retains_noop_only_stratum(tmp_path, monkeypatch):
    _fixture(tmp_path, monkeypatch)
    rows = [
        {"proposal_id": "p", "source": "s", "node": "n", "instance_seed": 1,
         "noop": False, "duplicate": False, "sigma_node": 1.0, "features": {}},
        {"proposal_id": "noop", "source": "other", "node": "n", "instance_seed": 2,
         "noop": True, "duplicate": False, "sigma_node": 1.0, "features": {}},
    ]
    monkeypatch.setattr(oe, "load_table", lambda _: rows)
    out = oe.assemble(tmp_path)
    assert {row["proposal_id"] for row in out} == {"p", "noop"}
    noop = next(row for row in out if row["proposal_id"] == "noop")
    assert noop["delta_true"] == 0 and noop["weight"] == 1


def test_evidence_full_population_has_unit_training_and_evaluation_weights(tmp_path, monkeypatch):
    audit = _fixture(tmp_path, monkeypatch)
    audit["reason"] = "full_population"
    (tmp_path / "audits.jsonl").write_text(json.dumps(audit) + "\n")
    row = oe.assemble(tmp_path)[0]
    assert row["weight"] == row["eval_weight"] == 1.0


def test_crossfit_never_passes_evaluation_values_to_models():
    class Inspect:
        def fit(self, rows):
            assert all("delta_true" not in r and "eval_weight" not in r for r in rows)
            assert all("delta_audit_all" not in r for r in rows)
            assert all(r.get("_evidence_seed_split") is True for r in rows)
            return self

        def predict(self, rows):
            assert all("delta_true" not in r and "eval_weight" not in r for r in rows)
            assert all("soft" not in r and "weight" not in r for r in rows)
            assert all(r.get("_evidence_seed_split") is True for r in rows)
            return np.zeros((len(rows), oe.N_BINS))

    rows = [{"node": "n", "instance_seed": i, "_evidence_seed_split": True,
             "features": {}, "soft": [0] * oe.N_BINS, "weight": 1,
             "delta_true": 123, "delta_audit_all": 456, "eval_weight": 1}
            for i in range(2)]
    oe.crossfit(rows, k=2, arms={"spy": Inspect})
