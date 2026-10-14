"""HTTP-only fake model for the marked desktop DRYRUN fixture; no inference."""
import json
import os
from pathlib import Path
import re
import platform
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODEL = 'qwen2.5-coder:7b'
DIGEST = 'dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364'
INACTIVE_SENT = set()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, value, stream=False):
        self.send_response(200)
        self.send_header('Content-Type', 'application/x-ndjson' if stream else 'application/json')
        self.end_headers()
        self.wfile.write((json.dumps(value) + '\n').encode())

    def do_GET(self):
        model = {'name': MODEL, 'model': MODEL, 'digest': DIGEST, 'size': 5560907776,
                 'size_vram': 5560907776, 'expires_at': '2099-01-01T00:00:00Z'}
        self.reply({'version': 'DRYRUN'} if self.path == '/api/version' else {'models': [model]})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        with Path(os.environ['R1_DRYRUN_ROOT'], 'fake_calls.jsonl').open('a') as f:
            f.write(json.dumps({'label': 'DRYRUN', 'path': self.path, 'seed': body.get('options', {}).get('seed'), 'request': body}) + '\n')
        if self.path == '/api/generate':
            self.reply({'model': MODEL, 'response': 'OK', 'done': True})
            return
        prompt = '\n'.join(m.get('content', '') for m in body.get('messages', []))
        trial = int(re.search(r'Budget index \(trial number\): (\d+)', prompt).group(1))
        if 'Node: openml_breast_w' in prompt:
            seed = body.get('options', {}).get('seed')
            inactive = trial == 3 and seed not in INACTIVE_SENT
            if inactive:
                INACTIVE_SENT.add(seed)
            key = 'max_depth' if inactive else 'C'
            old = re.search(r'^  C = (.+)$', prompt, re.M).group(1)
            value = str(0.001 * 2 ** (trial - 1)) if key == 'C' else '7'
        else:
            key = 'MAX_ITER'
            old = re.search(r'^  MAX_ITER = (.+)$', prompt, re.M).group(1)
            value = str(16 + trial * 4)
        proposal = {'summary': f'DRYRUN novel fixture proposal at trial {trial}',
                    'rationale': 'DRYRUN HTTP fixture; no inference', 'param': key,
                    'old_value': old, 'new_value': value,
                    'objective': f'Change {key} from {old} to {value}'}
        self.reply({'model': MODEL, 'created_at': '2026-10-14T00:00:00Z',
                    'message': {'role': 'assistant', 'content': json.dumps(proposal)},
                    'done': True, 'done_reason': 'stop', 'prompt_eval_count': 10,
                    'eval_count': 10, 'total_duration': 1000000}, bool(body.get('stream')))


if __name__ == '__main__':
    if platform.node().split('.')[0] == 'ucrtasl':
        raise SystemExit('STOP: fake Ollama is forbidden on Ada')
    if os.environ.get('R1_DRYRUN') != '1' or not Path(os.environ.get('R1_DRYRUN_ROOT', '/'), '.dryrun').is_file():
        raise SystemExit('STOP: fake Ollama requires a marked DRYRUN directory')
    ThreadingHTTPServer(('127.0.0.1', int(os.environ['R1_DRYRUN_PORT'])), Handler).serve_forever()
