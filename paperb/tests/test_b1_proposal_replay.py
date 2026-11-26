"""Test r1/scripts/b1_proposal_replay.py against the stand-in server (R1-EXAM-B1-MODEL-OUTPUT-INVALID item 1).

A root is produced by ``exam_truncation_driver.py``; the replay then rebuilds the prompts of chosen trials
from a copy of that root and must reproduce the recorded context, reply hashes and llm_call fields exactly,
and report the run guard's and the new pre-check's verdicts. AI-assisted (Claude)."""
from __future__ import annotations

import json
import os
import shutil
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

from r1.tests.test_exam_b1_truncation import _drive

REPO = Path(__file__).resolve().parents[2]


def test_replay_reproduces_recorded_calls_and_reports_the_guard(tmp_path, monkeypatch):
    plan = ['stop', 'stop', 'sym_not_editable', 'stop', 'stop']
    r = _drive(tmp_path, plan, TRUNC_NODE='digits_mlp', name='run')
    assert r['error'] is None
    copy = tmp_path / 'root_copy'
    shutil.copytree(tmp_path / 'run', copy)
    monkeypatch.syspath_prepend(str(REPO / 'r1/tests'))
    monkeypatch.syspath_prepend(str(REPO / 'r1/scripts'))
    import exam_truncation_driver as d
    d.PLAN[:] = ['stop', 'sym_not_editable', 'stop']       # one request per replayed trial: 2, 3, 4
    d.REQUESTS.clear()
    monkeypatch.setenv('R1_FAKE_OLLAMA_ROOT', str(tmp_path / 'fake'))
    server = ThreadingHTTPServer(('127.0.0.1', 0), d.StandIn)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        monkeypatch.setenv('LLAMACPP_BASE_URL', f'http://127.0.0.1:{server.server_address[1]}/v1')
        monkeypatch.delenv('LLAMACPP_CACHE_PROMPT', raising=False)
        from r1.scripts.b1_proposal_replay import replay
        report = replay(copy, 'standin_candidate', 'digits_mlp', 9001, [2, 3, 4], tmp_path / 'replay')
    finally:
        server.shutdown()
    by = {t['trial']: t for t in report['trials']}
    for b in (2, 3, 4):
        rep = by[b]['reproduced']
        assert rep['context_sha256'] is True and rep['raw_proposal_sha256'] is True, (b, rep)
        assert rep['incumbent_metric_matches_record'] is True
        assert all(a == b2 for a, b2 in rep['llm_call_event'].values()), rep['llm_call_event']
    assert by[2]['run_guard_verdict'] == 'pass' and by[2]['new_precheck'] is None
    assert by[3]['run_guard_verdict'] == 'STOP: B1 worker directive and structured edit differ'
    assert by[3]['new_precheck']['check'] == 'directive_symbol_not_editable' and by[3]['directive'][0] == 'momentum'
    assert by[3]['run_decision'] == 'failed_invalid' and by[3]['reply_fields']['param'] == 'MAX_ITER'
    assert json.loads((tmp_path / 'replay' / 'replay.json').read_text())['schema'] == 'b1_proposal_replay/v1'
    # the copy is unchanged by the replay
    for name in ('root_trials.jsonl', 'root_events.jsonl'):
        assert (copy / name).read_bytes() == (tmp_path / 'run' / name).read_bytes()
