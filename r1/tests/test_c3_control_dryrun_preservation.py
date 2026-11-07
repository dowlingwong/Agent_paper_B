"""Synthetic control DRYRUN must retain interrupted evidence and refuse a retry."""
import json

import pytest

from r1.scripts import c3_control_dryrun as dryrun


def test_archive_retains_complete_campaign_tree(tmp_path):
    campaign = tmp_path / "campaigns" / "A3__digits_mlp"
    campaign.mkdir(parents=True)
    (campaign / "trials.jsonl").write_bytes(b"partial\n")
    dryrun.archive_existing(tmp_path, campaign)
    assert not campaign.exists()
    retained = list((tmp_path / "_to_delete").glob("*/A3__digits_mlp/trials.jsonl"))
    assert len(retained) == 1 and retained[0].read_bytes() == b"partial\n"


def test_versioned_state_retains_old_bytes(tmp_path):
    state = tmp_path / "state.json"
    state.write_text("before")
    dryrun.write_versioned(tmp_path, state, "after")
    retained = list((tmp_path / "_to_delete").glob("*/state.json"))
    assert state.read_text() == "after"
    assert len(retained) == 1 and retained[0].read_text() == "before"


def test_only_recorded_synthetic_interruption_is_archived(tmp_path):
    name = "A3__digits_mlp"
    campaign = tmp_path / "campaigns" / name
    campaign.mkdir(parents=True)
    (campaign / "trials.jsonl").write_text("partial")
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"interruption": None}))
    with pytest.raises(SystemExit, match="preserve it"):
        dryrun.prepare_campaign_directory(tmp_path, campaign, name)
    assert (campaign / "trials.jsonl").read_text() == "partial"
    dryrun.write_versioned(tmp_path, state, json.dumps({"resume_started_utc": "now", "interruption":
                           {"signal": "SIGKILL (runner process group)", "in_progress": name}}))
    assert dryrun.prepare_campaign_directory(tmp_path, campaign, name)
    assert list(campaign.iterdir()) == []
    assert next((tmp_path / "_to_delete").glob("*/A3__digits_mlp/trials.jsonl")).read_text() == "partial"


def test_refuse_symlink_without_mutation(tmp_path):
    original = tmp_path / "original"
    original.write_text("keep")
    link = tmp_path / "link"
    link.symlink_to(original)
    with pytest.raises(SystemExit, match="symlink"):
        dryrun.archive_existing(tmp_path, link)
    assert link.is_symlink() and original.read_text() == "keep"


def test_resume_refuses_second_attempt_before_services(tmp_path, monkeypatch):
    state = {"interruption": {"signal": "SIGKILL (runner process group)", "in_progress": "A3__digits_mlp"},
             "resume_started_utc": "already attempted"}
    (tmp_path / "state.json").write_text(json.dumps(state))
    monkeypatch.setattr(dryrun, "start_services", lambda work: pytest.fail("services must not start"))
    with pytest.raises(SystemExit, match="already attempted"):
        dryrun.stage_resume(tmp_path, 1)
    assert json.loads((tmp_path / "state.json").read_text()) == state
