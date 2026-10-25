"""RUNBOOK Track H.4 (R1-SKIP-DISPLAY, author 25 Oct): the manager's memory shows a control-plane skip as one
line, "skipped by the control plane: predicted no gain", with no metric; manifests record the display version.
ENGINEERING_ONLY; AI-assisted (Claude)."""
from __future__ import annotations

import re

import numpy as np
import pytest

from r1.c3.control import SKIP_DISPLAY, RuleController, declare_skip_display
from r1.c3.prior_model import FixedPrior
from r1.headroom.scripted_manager import ScriptedRandomManager
from r1.tests.c3_campaign_fixtures import node_context, run_campaign

from autoresearch.memory.summarizer import SKIP_DISPLAY_TEXT

NOGAIN = np.array([0.30, 0.20, 0.20, 0.15, 0.10, 0.04, 0.01, 0.0, 0.0, 0.0, 0.0, 0.0])


class Recording(ScriptedRandomManager):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.contexts = []

    def propose_next_trial(self, status, memory_context, node_spec):
        self.contexts.append(memory_context.context_text)
        return super().propose_next_trial(status, memory_context, node_spec)


@pytest.mark.parametrize("memory_mode", ["append_only_summary", "append_only_summary_with_rationale"])
def test_skipped_proposals_show_one_line_without_metric(tmp_path, memory_mode):
    ctl = RuleController(FixedPrior(NOGAIN, "A3"), node_context(0.005, memory_mode=memory_mode))
    backend = Recording("digits_mlp", seed=5, repetition=0)
    _, events, rows, _ = run_campaign(tmp_path, backend, budget=5, memory_mode=memory_mode, **ctl.campaign_kwargs())
    assert [r["decision"] for r in rows] == ["kept", "skipped", "skipped", "skipped", "skipped"]
    last = backend.contexts[-1].splitlines()  # memory before trial 5: trial 1 plus three skips
    skip_lines = [line for line in last if SKIP_DISPLAY_TEXT in line]
    assert len(skip_lines) == 3
    for row, line in zip(rows[1:4], skip_lines):
        assert line == f"{row['trial_id']}: summary={row['proposal_summary']}; {SKIP_DISPLAY_TEXT}"
        assert not re.search(r"metric|delta|rationale|0\.\d{3}", line)
    assert sum(SKIP_DISPLAY_TEXT in line for line in last) == 3 and len([x for x in last if "decision=skipped" in x]) == 0
    started = [e for e in events if e["event_type"] == "campaign_started"][0]["payload"]
    assert started["skip_display"] == SKIP_DISPLAY == "one_line/v1"


def test_manifest_records_the_display_version():
    manifest = {"label": "DRYRUN"}
    assert declare_skip_display(manifest) == "one_line/v1" and manifest["skip_display"] == "one_line/v1"
    assert declare_skip_display(manifest) == "one_line/v1"  # idempotent
    with pytest.raises(ValueError):
        declare_skip_display({"skip_display": "historical"})
    with pytest.raises(ValueError):
        declare_skip_display({}, "two_lines/v9")
    assert RuleController(FixedPrior(NOGAIN), node_context(0.005)).campaign_kwargs()["skip_display"] == "one_line/v1"
