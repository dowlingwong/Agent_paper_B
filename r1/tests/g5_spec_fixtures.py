"""Build the unsigned G.5 test state from the shared spec structure."""

import json
from pathlib import Path

import pytest

G5_SPEC_PATH = Path(__file__).resolve().parents[2] / "sweep2/t1_tasl/g5_tasl_spec.json"


def draft_spec():
    """Restore the draft fields used by the option, guard and note-render tests."""
    spec = json.loads(G5_SPEC_PATH.read_text())
    spec["run_id"] = "PENDING: c3_t1_labels_YYYYMMDD (the signed note's date)"
    spec["paper"]["commit"] = "PENDING: the commit that publishes the signed G.5 note and this spec"
    spec["decisions_row"] = "PENDING: the author's PLAN row signing the section 11 decisions"
    spec["e4_amendment_row"] = "PENDING: G5-MEM A needs the author's PLAN row amending E4's 'both memory modes'"
    for decision in spec["decisions"].values():
        decision["option"] = decision["recommended"]
        decision["signed"] = False
    spec["noise_floor"]["seven"].update({
        "copy": "PENDING: the reviewed REL-T1-G1B copy of the g1b-tasl-20261121-b summary (joined under G1B-JOIN)",
        "sha256": "PENDING",
        "review": "PENDING",
        "sealed_path": "PENDING: the sealed summary.json the copy was taken from",
        "gate_copy": "PENDING: the copy of crosscheck_gate.json, beside the summary copy",
        "gate_sha256": "PENDING",
        "assembly_copy": "PENDING: the copy of the run's ASSEMBLY.json, beside the summary copy (D6 A, R1-T1-FEAT-DECISIONS)",
        "assembly_sha256": "PENDING",
        "runs_copy": "PENDING: the copy of the run's runs.jsonl, beside the summary copy (D6 A, R1-T1-FEAT-DECISIONS)",
        "runs_sha256": "PENDING",
    })
    spec["key_values"]["freeze_wait_release_date"] = "2026-12-18"
    spec["key_values"]["cuda_ipc"]["mode"] = "PENDING: c12 | acceptance"
    for node in spec["nodes"]:
        if node["family"] == "G5-7":
            node["tails"] = "PENDING: P10 (Gaussian or Student-t from the seven-node G.1b summary)"
            node.pop("tails_nu", None)
    return spec


@pytest.fixture
def draft_spec_path(tmp_path):
    path = tmp_path / "g5_draft_spec.json"
    path.write_text(json.dumps(draft_spec()), encoding="utf-8")
    return path
