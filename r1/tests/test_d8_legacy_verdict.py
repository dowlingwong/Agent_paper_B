"""Synthetic checks: R1-BX-D8 supersedes the legacy per-node verdict."""
import json
from pathlib import Path
from unittest.mock import patch

from r1.c3 import offline_eval


class Poison:
    def __getitem__(self, key):
        raise AssertionError("the legacy gate must not inspect evaluation data")


def test_superseded_gate_never_returns_a_pass_or_consumes_evaluation():
    result = offline_eval.gate_verdict(Poison())
    assert result["verdict"] == "NOT_AVAILABLE"
    assert "R1-BX-D8" in result["reason"]
    assert "pass" not in result and "nodes_meeting_criterion" not in result


def test_cli_reports_unavailable_without_a_legacy_pass(capsys):
    evaluation = {"g_declaration": {}, "run_accounting": {}}
    written = []
    with patch.object(offline_eval, "table_noise", return_value=None), \
         patch.object(offline_eval, "assemble", return_value=[]), \
         patch.object(offline_eval, "evaluate", return_value=evaluation), \
         patch.object(offline_eval, "sensitivity_view", return_value={}), \
         patch.object(Path, "write_text", lambda self, text: written.append(text)):
        assert offline_eval.main(["--table", "/synthetic/table", "--out", "/synthetic/out"]) == 0
    output = json.loads(written[0])
    assert output["gate"]["verdict"] == "NOT_AVAILABLE"
    assert "pass" not in output["gate"]
    assert json.loads(capsys.readouterr().out)["gate_verdict"] == "NOT_AVAILABLE"
