import json
from pathlib import Path

import pytest

from paperc import incumbent_audits as audits


def test_replay_includes_trial_one_and_keeps_the_final_files():
    rows = [{"budget_index": i, "decision": "discarded"} for i in range(1, 21)]
    for index, old, new in ((0, 2, 4), (7, 4, 8)):
        rows[index] = {"budget_index": index + 1, "decision": "kept",
                       "delta_vs_best": 0.5 if index else None,
                       "extra": {"manager": {"structured_edit": {"path": "train.py", "symbol": "WIDTH",
                                                                 "old": old, "new": new}}}}
    got = audits.replay_retained(rows, {"train.py": "WIDTH = 2\n"}, "digits_mlp", "digits_mlp__s17", "none")
    assert [r["trial"] for r in got["retained"]] == [1, 8]
    assert got["retained"][0]["previous"] == got["start"]
    assert got["retained"][1]["previous"] == got["retained"][0]["candidate"]
    assert got["configs"][got["terminal"]] == {"train.py": "WIDTH = 8\n"}
    with pytest.raises(ValueError, match="exactly 20"):
        audits.replay_retained(rows[:-1], {}, "digits_mlp", "digits_mlp__s17", "none")


def test_registry_check_refuses_overlap(tmp_path):
    registry = Path(__file__).resolve().parents[1] / "seeds" / "registry_v1.json"
    audits.check_seeds(registry, 72)
    altered = json.loads(registry.read_bytes())
    altered["paper_b"].append({"name": "collision", "lo": audits.AUDIT_START + 1, "hi": audits.AUDIT_START + 2})
    copy = tmp_path / "registry.json"
    copy.write_text(json.dumps(altered))
    with pytest.raises(ValueError, match="collision"):
        audits.check_seeds(copy, 72)


def test_stakes_uses_either_floor_and_keeps_trial_one_separate():
    root = {"node": "digits_mlp", "mode": "none", "audit_seeds": [1, 2], "start": "s", "terminal": "u",
            "retained": [{"trial": 1, "previous": "s", "candidate": "t", "recorded_delta": None},
                         {"trial": 3, "previous": "t", "candidate": "u", "recorded_delta": 1.0}]}
    values = {("digits_mlp", (1, 2), key): [{"metric": a}, {"metric": b}]
              for key, (a, b) in {"s": (2, 3), "t": (1, 2), "u": (1, 2)}.items()}
    c1 = {"nodes": {"digits_mlp": {"edits": [{"decision_regret": 0.15}]}}}
    summary, = audits.summarise([root], values, {"digits_mlp": {"sigma_node": 1.0}}, c1)
    assert summary["stakes_floor"] and summary["kept_increment_sigma_d"] == 0
    assert summary["terminal_gain_median"] == summary["first_keep_median"] == -1
    assert summary["false_keeps"] == summary["subsequent_keeps"] == 1


def test_unpublished_or_wrong_note_cannot_create_job_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(audits.audit, "_published_bytes", lambda *args: b"approved: false\n")
    out, scratch = tmp_path / "output", tmp_path / "scratch"
    with pytest.raises(ValueError, match="published authorization"):
        audits.run(Path.cwd(), b'{}', scratch, out)
    assert not out.exists() and not scratch.exists()
