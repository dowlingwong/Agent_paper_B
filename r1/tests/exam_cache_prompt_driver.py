"""Subprocess driver for test_exam_b1_cache_prompt: one exam-shaped campaign root against a stand-in
llama-server, under the harness pin named by AR_HARNESS_ROOT.  No inference, no GPU, no network
beyond 127.0.0.1.  ENGINEERING_ONLY; AI-assisted (Claude).

It builds the proposer with ``r1.exam.campaign.exam_manager`` (the factory ``collect`` uses), runs the
harness ``run_real_campaign`` with the same manager/memory/split/budget arguments as ``collect`` (whose
evidence body is still behind its B1/B2 STOP), and writes ``out/result.json`` with the stand-in's request
bodies, the ``llm_call`` payloads and the ``cache_prompt`` manifest field from
``r1.exam.campaign.cache_prompt_evidence`` (or the STOP it raised).
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


class StandIn(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):
        pass

    def do_POST(self):
        import c3_fake_ollama as fake
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])) or b'{}')
        REQUESTS.append({'path': self.path, 'body': body})
        prompt = body['messages'][-1]['content']
        content = json.dumps(fake.proposal_for(prompt, body.get('seed')))
        data = json.dumps({'id': 'x', 'object': 'chat.completion', 'created': 1, 'model': body.get('model'),
                           'choices': [{'index': 0, 'finish_reason': 'stop',
                                        'message': {'role': 'assistant', 'content': content}}],
                           'usage': {'prompt_tokens': 7, 'completion_tokens': 5, 'total_tokens': 12}}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)


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
    from autoresearch.memory.event_store import CampaignEventStore
    from autoresearch.nodes.registry import load_registered_node
    node, seed, W, cap = 'digits_mlp', 9001, 3, 8
    spec = load_registered_node(node, repo_root=c.HARNESS)
    root = out / 'node'
    shutil.copytree(c.HARNESS / 'nodes' / node, root, ignore=shutil.ignore_patterns('__pycache__', '.autoresearch_artifacts'))
    manager = c.exam_manager({'id': 'standin_candidate'}, 'manager_proposal/v1', journal_path=out / 'b1_proposals.jsonl')
    worker = c.FixtureWorker(root, seed)
    manager.b1_worker = worker   # as collect sets it (R1-EXAM-B1-MODEL-OUTPUT-INVALID)
    run_real_campaign(node_spec=spec, campaign_id=f'{node}__s{seed}', budget=cap, manager_mode='baseline_manager',
                      memory_mode='append_only_summary', records_path=out / 'root_trials.jsonl',
                      worker=worker, proposal_backend=manager,
                      compute_budget=ComputeBudget(max_worker_runs=W, max_llm_calls=cap),
                      action_versions=ActionVersions.new_campaign(), verify_split_policy='vary',
                      event_store=CampaignEventStore(out / 'root_events.jsonl'), proposal_observer=None)
    server.shutdown()
    records = c.read_rows(out / 'root_trials.jsonl')
    events = c.read_rows(out / 'root_events.jsonl')
    try:
        manifest_field, stop = c.cache_prompt_evidence(records, events), None
    except RuntimeError as exc:
        manifest_field, stop = None, str(exc)
    from r1.harness import harness_commit
    result = {'harness': harness_commit(), 'requests': REQUESTS,
              'llm_call_events': [e['payload'] for e in events if e['event_type'] == 'llm_call'],
              'trial_llm_calls': [((r.get('extra') or {}).get('manager') or {}).get('llm_call') for r in records],
              'manifest_cache_prompt': manifest_field, 'stop': stop}
    (out / 'result.json').write_text(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main(sys.argv[1])
