"""Branch ledgers must survive outcome collection for DT3 provenance checks."""
import json
from pathlib import Path
from types import SimpleNamespace
from r1.headroom import e1b_collect as collect

def test_run_leaf_retains_branch_ledger_after_audit(tmp_path, monkeypatch):
    work, out = tmp_path / "work", tmp_path / "out"
    (out / "leaves").mkdir(parents=True)
    spec = collect.load_registered_node("digits_mlp", repo_root=collect.HARNESS)
    snapshot = SimpleNamespace(budget_index=4, ledger_prefix=[])
    monkeypatch.setattr(collect, "read_snapshot", lambda p: snapshot)
    monkeypatch.setattr(collect, "_audit", lambda *a: [0.8, 0.9])
    def resume(snapshot, into, **kwargs):
        into.mkdir(parents=True)
        for rel in spec.editable_paths:
            target = into / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text((collect.HARNESS / "nodes/digits_mlp" / rel).read_text())
        ledger = into / "branch_trials.jsonl"
        ledger.write_text(json.dumps({"decision": "kept", "extra": {}, "proposal_summary": "LLM proposal"}) + "\n")
        return SimpleNamespace(first_record=SimpleNamespace(extra={"control": {"action": "continue"}}),
                               restored=SimpleNamespace(records_path=ledger))
    monkeypatch.setattr(collect, "resume_campaign", resume)
    leaf = collect.run_leaf("unused", "fixture", "digits_mlp", "continue", 1, 101, 2, str(work), str(out))
    assert leaf["integrity"] == "ok"
    ledger = work / "branches" / leaf["leaf_id"] / "branch_trials.jsonl"
    assert json.loads(ledger.read_text())["proposal_summary"] == "LLM proposal"
