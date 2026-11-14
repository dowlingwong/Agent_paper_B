"""Subprocess driver for test_exam_b2_collect: one B2-phase campaign root through ``r1.exam.campaign.collect``
(the reviewed B1/B2 collector) against a loopback stand-in server, under the harness pin named by AR_HARNESS_ROOT.
DRYRUN fixture worker and audits; no inference, no GPU.  ENGINEERING_ONLY; AI-assisted (Claude), B2 code unit.

Environment:
  B2_PLAN      JSON list of proposer reply kinds in order (``exam_truncation_driver`` kinds: "stop",
               "length_partial", "sym_differs", "ctx_overflow", "http500", "surrogate", ...); later requests "stop".
  B2_OBSERVER  "ok" (default) or "fail" (the first A4 observer request gets HTTP 503).
  B2_FAULT     "" (default), "final_none" (one final-Y audit seed returns no metric), "audit_none" (one
               per-proposal audit seed returns no metric).
  B2_TRIALS    LLM-call cap (default 10); B2_W worker cap (default 3).
Writes ``root/driver_result.json``: status, exception, requests, records, the campaign manifest if any.
"""
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'r1/scripts')); sys.path.insert(0, str(ROOT / 'r1/tests'))
import exam_truncation_driver as trunc   # noqa: E402  (mutate, COMPLETION_TOKENS; its main() is not run)

PLAN = json.loads(os.environ.get('B2_PLAN', '[]'))
OBSERVER = os.environ.get('B2_OBSERVER', 'ok')
FAULT = os.environ.get('B2_FAULT', '')
REQUESTS = []
PROPOSER_INDEX = [0]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code, payload):
        data = json.dumps(payload).encode()
        self.send_response(code); self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)

    def do_POST(self):
        import c3_fake_ollama as fake
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        prompt = body['messages'][-1]['content']
        observer = prompt.startswith('You proposed the edit below.')
        if observer:
            REQUESTS.append({'observer': True, 'kind': OBSERVER, 'body': body})
            if OBSERVER == 'fail':
                self.send_response(503); self.send_header('Content-Length', '0'); self.end_headers(); return
            answer = {'p_no_effect': 0.2, 'p_positive': 0.7, 'size': 'small'}
            return self._send(200, {'id': 'f', 'object': 'chat.completion', 'created': 1, 'model': body['model'],
                                    'choices': [{'index': 0, 'finish_reason': 'stop',
                                                 'message': {'role': 'assistant', 'content': json.dumps(answer)}}],
                                    'usage': {'prompt_tokens': 7, 'completion_tokens': 5, 'total_tokens': 12}})
        index = PROPOSER_INDEX[0]; PROPOSER_INDEX[0] += 1
        kind = PLAN[index] if index < len(PLAN) else 'stop'
        REQUESTS.append({'observer': False, 'kind': kind, 'body': body})
        if kind == 'ctx_overflow':
            return self._send(400, {'error': {'code': 400, 'type': 'exceed_context_size_error', 'n_prompt_tokens': 40000,
                                              'n_ctx': 32768, 'message': 'request (40000 tokens) exceeds the available '
                                              'context size (32768 tokens), try increasing it'}})
        if kind == 'http500':
            return self._send(500, {'error': 'stand-in failure'})
        proposal = fake.proposal_for(prompt, body.get('seed'))
        trunc.mutate(kind, proposal, prompt)
        content, finish = json.dumps(proposal), 'stop'
        if kind == 'length_partial':
            content, finish = content[:40], 'length'
        message = {'role': 'assistant', 'content': content}
        completion = trunc.COMPLETION_TOKENS.get(kind, 5)
        return self._send(200, {'id': 'x', 'object': 'chat.completion', 'created': 1, 'model': body['model'],
                                'choices': [{'index': 0, 'finish_reason': finish, 'message': message}],
                                'usage': {'prompt_tokens': 7, 'completion_tokens': completion, 'total_tokens': 7 + completion}})


def main(root):
    root = Path(root); root.mkdir(parents=True, exist_ok=True); (root / '.dryrun').write_text('synthetic')
    out = root / 'root'; out.mkdir()
    os.environ['R1_FAKE_OLLAMA_ROOT'] = str(root)
    for key in ('LLAMACPP_CACHE_PROMPT', 'OPENAI_API_KEY', 'OPENAI_BASE_URL'):
        os.environ.pop(key, None)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_address[1]}/v1'
    os.environ['LLAMACPP_BASE_URL'] = url
    from r1.exam import campaign
    from r1.exam.observer import B1ObserverFatal
    if FAULT:
        original = campaign.fixture_metric
        phase = {'final': False}
        if FAULT == 'final_none':
            # Per-proposal audits are complete; the final-Y audit (after cache_prompt evidence) loses seed 9205.
            evidence = campaign.cache_prompt_evidence
            def mark(*a, **k):
                phase['final'] = True
                return evidence(*a, **k)
            campaign.cache_prompt_evidence = mark
        def metric(files, seed):
            if FAULT == 'audit_none' and seed == 9205: return None
            if FAULT == 'final_none' and phase['final'] and seed == 9205: return None
            return original(files, seed)
        campaign.fixture_metric = metric
    job = {'out': str(out), 'binding': 'fixture', 'workers': 1, 'host': 'fixture', 'phase': 'b2', 'node': 'digits_mlp',
           'seed': 9011, 'candidate': {'id': 'standin_candidate'}, 'mode': 'off', 'dryrun': True,
           'W': int(os.environ.get('B2_W', 3)), 'llm_call_cap': int(os.environ.get('B2_TRIALS', 10)),
           'audit_seeds': list(range(9201, 9211)), 'base_url': url, 'value_grids': str(ROOT / 'r1/exam/value_grids.yaml'),
           'proposal_schema': 'manager_proposal/v1',
           'authority_config': {'dryrun': True, 'dryrun_root': str(root), 'rule_sha256': 'fixture'}}
    (out / 'job.json').write_text(json.dumps(job))
    status, error = 'complete', None
    try:
        try:
            campaign.collect(job)
        except B1ObserverFatal as exc:
            status, error = 'observer_stop', f'{type(exc).__name__}: {exc}'
        except Exception as exc:
            status, error = 'stop', f'{type(exc).__name__}: {exc}'
    finally:
        server.shutdown(); server.server_close()
    records = campaign.read_rows(out / 'root_trials.jsonl') if (out / 'root_trials.jsonl').exists() else []
    manifest = json.loads((out / 'campaign_manifest.json').read_text()) if (out / 'campaign_manifest.json').exists() else None
    journal = campaign.read_rows(out / 'b1_proposals.jsonl') if (out / 'b1_proposals.jsonl').exists() else []
    (root / 'driver_result.json').write_text(json.dumps({'status': status, 'error': error, 'requests': REQUESTS,
                                                         'records': records, 'manifest': manifest, 'journal': journal},
                                                        default=str))


if __name__ == '__main__':
    main(sys.argv[1])
