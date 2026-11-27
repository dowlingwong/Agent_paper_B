"""local/20261127-02: ``trackp.py sft-select`` with a missing or unreadable runs path is a protocol STOP (rc 2, ``STOP:``)
before any read, also with a filled host config (which no longer stops at the placeholder check first)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "r1" / "scripts"))
import trackp  # noqa: E402


def _filled_config(tmp_path: Path) -> Path:
    """The repository's HTCondor host config with every TODO_VERIFY* value replaced (a stand-in for the filled one)."""
    from r1.c3.train import run as R

    def fill(obj):
        if isinstance(obj, dict):
            return {k: (v if k == "comment" else fill(v)) for k, v in obj.items()}
        if isinstance(obj, list):
            return [fill(v) for v in obj]
        if isinstance(obj, str) and obj.startswith(R.PLACEHOLDER):
            return "filled-for-test"
        return obj
    cfg = fill(json.loads((ROOT / "r1/scripts/configs/trackp_htcondor_v2.json").read_text()))
    assert R.placeholders(cfg) == []
    out = tmp_path / "filled.json"
    out.write_text(json.dumps(cfg))
    return out


def _run(tmp_path, capsys, runs):
    cfg = _filled_config(tmp_path)
    rc = trackp.main(["--config", str(cfg), "sft-select", "--runs", *map(str, runs), "--run-dir", str(tmp_path / "sel")])
    return rc, capsys.readouterr().err


def test_missing_runs_path_is_a_protocol_stop_with_a_filled_config(tmp_path, capsys):
    rc, err = _run(tmp_path, capsys, [tmp_path / "missing"])
    assert rc == 2 and "STOP: sft-select: run report missing or unreadable" in err


def test_unreadable_run_report_is_a_protocol_stop(tmp_path, capsys):
    run = tmp_path / "run1" / "stage_s"
    run.mkdir(parents=True)
    (run / "sft_report.json").write_text("{not json")
    rc, err = _run(tmp_path, capsys, [tmp_path / "run1"])
    assert rc == 2 and "JSONDecodeError" in err


def test_one_bad_run_among_good_ones_stops_before_select(tmp_path, capsys, monkeypatch):
    from r1.c3.train import sft as SFT
    good = tmp_path / "good" / "stage_s"
    good.mkdir(parents=True)
    (good / "sft_report.json").write_text(json.dumps({"stage": "s"}))
    called = []
    monkeypatch.setattr(SFT, "select_lr", lambda dirs: called.append(dirs) or {})
    rc, err = _run(tmp_path, capsys, [tmp_path / "good", tmp_path / "missing"])
    assert rc == 2 and called == [] and "missing" in err
