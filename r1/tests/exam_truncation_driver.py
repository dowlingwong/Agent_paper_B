"""Subprocess driver for test_exam_b1_truncation: one exam-shaped campaign root against a stand-in
llama-server that can cut replies short, under the harness pin named by AR_HARNESS_ROOT.  No inference,
no GPU, no network beyond 127.0.0.1.  ENGINEERING_ONLY; AI-assisted (Claude).

Like ``exam_cache_prompt_driver.py``: the proposer comes from ``r1.exam.campaign.exam_manager`` (the factory
``collect`` uses) and the root runs the harness ``run_real_campaign`` with ``collect``'s manager / memory /
split / budget arguments and the synthetic ``FixtureWorker``.

Environment:
  TRUNC_PLAN     JSON list of reply kinds, one per request in order (later requests: "stop"):
                 "stop"            a valid proposal, finish_reason "stop"
                 "length_partial"  the first 40 characters of a valid proposal, finish_reason "length"
                 "length_full"     a complete valid proposal, finish_reason "length" (must still be invalid)
                 "length_empty"    empty content, finish_reason "length" (cut during thinking)
                 "content_filter"  a complete valid proposal, finish_reason "content_filter"
                 "http500"         HTTP 500 (any other failure must still stop the root)
                 Model-output kinds (R1-EXAM-B1-MODEL-OUTPUT-INVALID; finish_reason "stop"; fields valid, objective or
                 value altered): "no_directive", "sym_not_editable", "sym_differs", "old_differs", "new_differs",
                 "backslash", "py_long", "py_nonliteral", "py_nonfinite", "py_bool", "stale_and_mismatch"
                 (the harness precondition rejects it first), "inactive_and_mismatch" (openml: a D25 inactive key),
                 "unknown_param" (the param names no editable constant), "ctx_overflow" (llama-server's HTTP 400 for
                 a prompt longer than the context), "mismatch_inactive_objective" (openml: structured edit on the active C,
                 objective naming the D25-inactive max_depth), "surrogate" (a lone surrogate escape in a reply field)
  TRUNC_MANAGER  "fix" (default): ``exam_manager``; "pin": the plain harness ``LangGraphManager`` built exactly
                 as ``exam_manager`` built it before R1-EXAM-B1-TRUNCATION-INVALID.
  TRUNC_NODE     node (default digits_mlp; openml_credit_approval has D25 active keys, and the stand-in names an
                 inactive key once at trial 3, so the next request is a D25 revision)
  TRUNC_TRIALS   trial budget (default 8);  TRUNC_LLM_CAP  LLM-call cap (default 8);  TRUNC_W  worker cap (default 3)
  TRUNC_OBSERVER "1": a stub A4 observer (one charged call after each worker run, as the exam's), else none
Writes ``out/result.json``: request bodies, records, events, the exception (if any), the cache_prompt field.
"""
from __future__ import annotations
import json
import os
import shutil
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / 'r1/scripts'))

REQUESTS: list = []
PLAN: list = json.loads(os.environ.get('TRUNC_PLAN', '[]'))
def _directive(p):
    return f"Change {p['param']} from {p['old_value']} to {p['new_value']}"


def mutate(kind, p, prompt):
    """Alter a valid stand-in proposal into one model-output fault (see the module docstring)."""
    import re
    openml = 'Node: openml_' in prompt
    other = 'max_iter' if openml else 'BATCH_SIZE'
    if kind == 'no_directive':
        p['objective'] = f"Increase {p['param']} a little to improve the metric."
    elif kind == 'sym_not_editable':
        p['objective'] = f"Change {'alpha' if openml else 'momentum'} from {p['old_value']} to {p['new_value']}"
    elif kind == 'sym_differs':
        p['objective'] = f"Change {other} from {p['old_value']} to {p['new_value']}"
    elif kind == 'old_differs':
        p['objective'] = f"Change {p['param']} from {p['old_value']}0 to {p['new_value']}"
    elif kind == 'new_differs':
        p['objective'] = f"Change {p['param']} from {p['old_value']} to {p['new_value']}5"
    elif kind == 'backslash':
        p['new_value'] = p['new_value'] + '\\1'
        p['objective'] = _directive(p)
    elif kind in ('py_long', 'py_nonliteral', 'py_nonfinite', 'py_bool'):
        p['new_value'] = {'py_long': '1' * 300, 'py_nonliteral': '2*16', 'py_nonfinite': '1e999', 'py_bool': 'True'}[kind]
        p['objective'] = _directive(p)
    elif kind == 'stale_and_mismatch':
        p['old_value'] = p['old_value'] + '9'
        p['objective'] = f"Change {other} from 1 to 2"
    elif kind == 'inactive_and_mismatch':
        found = re.search(r'^  max_depth = (.+)$', prompt, re.M)
        p['param'], p['old_value'], p['new_value'] = 'max_depth', found.group(1) if found else '5', '9'
        p['objective'] = f"Change C from 1 to 2"
    elif kind == 'mismatch_inactive_objective':   # openml: edit on the active C, objective names the inactive max_depth
        p['objective'] = f"Change max_depth from 5 to 9"
    elif kind == 'surrogate':                     # a lone surrogate in a reply field (JSON escape \\ud800)
        p['summary'] = p['summary'] + '\ud800'
    elif kind == 'unknown_param':
        p['param'] = 'momentum'
        p['objective'] = _directive(p)
    elif kind not in ('stop', 'length_partial', 'length_full', 'length_empty', 'content_filter', 'http500', 'ctx_overflow'):  # noqa
        raise ValueError(f'unknown stand-in kind {kind}')


COMPLETION_TOKENS = {'stop': 5, 'length_partial': 16384, 'length_full': 16384, 'length_empty': 16384,
                     'content_filter': 9}


class StandIn(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):
        pass

    def do_POST(self):
        import c3_fake_ollama as fake
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])) or b'{}')
        index = len(REQUESTS)
        kind = PLAN[index] if index < len(PLAN) else 'stop'
        REQUESTS.append({'path': self.path, 'body': body, 'kind': kind})
        if kind == 'ctx_overflow':   # llama.cpp 620d222's reply to a prompt longer than the context
            data = json.dumps({'error': {'code': 400, 'type': 'exceed_context_size_error', 'n_prompt_tokens': 40000, 'n_ctx': 32768,
                                         'message': 'request (40000 tokens) exceeds the available context size '
                                                    '(32768 tokens), try increasing it'}}).encode()
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if kind == 'http500':
            data = b'{"error": "stand-in failure"}'
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        prompt = body['messages'][-1]['content']
        proposal = fake.proposal_for(prompt, body.get('seed'))
        mutate(kind, proposal, prompt)
        content = json.dumps(proposal)
        finish = 'stop'
        if kind == 'length_partial':
            content, finish = content[:40], 'length'
        elif kind == 'length_full':
            finish = 'length'
        elif kind == 'length_empty':
            content, finish = '', 'length'
        elif kind == 'content_filter':
            finish = 'content_filter'
        message = {'role': 'assistant', 'content': content}
        if kind.startswith('length'):
            message['reasoning_content'] = 'r' * 123
        completion = COMPLETION_TOKENS.get(kind, 5)
        data = json.dumps({'id': 'x', 'object': 'chat.completion', 'created': 1, 'model': body.get('model'),
                           'choices': [{'index': 0, 'finish_reason': finish, 'message': message}],
                           'usage': {'prompt_tokens': 7, 'completion_tokens': completion,
                                     'total_tokens': 7 + completion}}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class StubObserver:
    """Stands in for the exam's A4 observer: same version and charge, a fixed answer, no request."""
    version = 'exam_self_forecast/v1'
    llm_calls_per_observation = 1

    def observe(self, proposal, status, node_spec):
        return {'status': 'ok', 'p_no_effect': 0.5, 'p_delta_positive': 0.25, 'llm_calls': 1}


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    os.environ['R1_FAKE_OLLAMA_ROOT'] = str(out)
    for key in ('LLAMACPP_CACHE_PROMPT', 'LLAMACPP_API_KEY', 'OPENAI_API_KEY', 'OPENAI_BASE_URL'):
        os.environ.pop(key, None)
    server = ThreadingHTTPServer(('127.0.0.1', 0), StandIn)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    os.environ['LLAMACPP_BASE_URL'] = f'http://127.0.0.1:{server.server_address[1]}/v1'
    from r1.exam import campaign as c
    from autoresearch.control_plane.action_versions import ActionVersions
    from autoresearch.control_plane.budget import ComputeBudget
    from autoresearch.control_plane.campaign import run_real_campaign
    from autoresearch.manager.langgraph_manager import LangGraphManager
    from autoresearch.memory.event_store import CampaignEventStore
    from autoresearch.nodes.registry import load_registered_node
    node, seed = os.environ.get('TRUNC_NODE', 'digits_mlp'), 9001
    W, trials, cap = (int(os.environ.get(k, d)) for k, d in (('TRUNC_W', 3), ('TRUNC_TRIALS', 8), ('TRUNC_LLM_CAP', 8)))
    spec = load_registered_node(node, repo_root=c.HARNESS)
    root = out / 'node'
    shutil.copytree(c.HARNESS / 'nodes' / node, root, ignore=shutil.ignore_patterns('__pycache__', '.autoresearch_artifacts'))
    if os.environ.get('TRUNC_MANAGER', 'fix') == 'pin':
        manager = LangGraphManager(model='llamacpp/standin_candidate', proposal_schema='manager_proposal/v1',
                                   transport_retry=None)
    else:
        manager = c.exam_manager({'id': 'standin_candidate'}, 'manager_proposal/v1', journal_path=out / 'b1_proposals.jsonl')
    worker = c.FixtureWorker(root, seed)
    if os.environ.get('TRUNC_ASSERT_JOURNAL') == '1':
        inner = worker.run_trial

        def run_trial(proposal, node_spec, budget_index):
            # The journal row of this proposal must be on disk before anything executes.
            rows = c.read_rows(out / 'b1_proposals.jsonl') if (out / 'b1_proposals.jsonl').exists() else []
            if (not rows or rows[-1]['budget_index'] != budget_index or rows[-1]['objective'] != proposal.objective
                    or rows[-1]['final_structured_edit'] != proposal.extra.get('structured_edit')):
                raise SystemExit('journal row missing before execution')
            return inner(proposal, node_spec, budget_index)
        worker.run_trial = run_trial
    if os.environ.get('TRUNC_MANAGER', 'fix') != 'pin':
        manager.b1_worker = worker
    error = None
    try:
        run_real_campaign(node_spec=spec, campaign_id=f'{node}__s{seed}', budget=trials, manager_mode='baseline_manager',
                          memory_mode='append_only_summary', records_path=out / 'root_trials.jsonl',
                          worker=worker, proposal_backend=manager,
                          compute_budget=ComputeBudget(max_worker_runs=W, max_llm_calls=cap),
                          action_versions=ActionVersions.new_campaign(), verify_split_policy='vary',
                          event_store=CampaignEventStore(out / 'root_events.jsonl'),
                          proposal_observer=StubObserver() if os.environ.get('TRUNC_OBSERVER') == '1' else None)
    except Exception as exc:   # recorded for the test; the real worker would exit 1 here
        error = {'type': type(exc).__name__, 'module': type(exc).__module__, 'message': str(exc)[:300]}
    server.shutdown()
    records = c.read_rows(out / 'root_trials.jsonl') if (out / 'root_trials.jsonl').exists() else []
    events = c.read_rows(out / 'root_events.jsonl') if (out / 'root_events.jsonl').exists() else []
    try:
        manifest_field, stop = c.cache_prompt_evidence(records, events), None
    except RuntimeError as exc:
        manifest_field, stop = None, str(exc)
    journal = None
    if (out / 'b1_proposals.jsonl').exists():
        from r1.exam.b1_proposal_journal import validate_proposal_journal
        try:
            journal = validate_proposal_journal(out / 'b1_proposals.jsonl', records, events)
        except RuntimeError as exc:
            journal = {'stop': str(exc)}
    from r1.harness import harness_commit
    result = {'journal_evidence': journal,
              'journal': c.read_rows(out / 'b1_proposals.jsonl') if (out / 'b1_proposals.jsonl').exists() else [],'harness': harness_commit(), 'requests': REQUESTS, 'records': records, 'events': events,
              'error': error, 'manifest_cache_prompt': manifest_field, 'cache_stop': stop}
    (out / 'result.json').write_text(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main(sys.argv[1])
