"""HTTP-only fake Ollama for the C3 sweep desktop DRYRUN and tests; no inference.

Invoked like the real binary (``c3_fake_ollama.py serve`` / ``pull <model>``);
it listens on ``$OLLAMA_HOST``.  Refuses on Ada and outside a marked DRYRUN
directory (``$R1_FAKE_OLLAMA_ROOT/.dryrun``).  Every request is logged to
``$R1_FAKE_OLLAMA_ROOT/fake_calls.jsonl``.

Fault injection (``$C3_FAKE_FAULTS``, a JSON list), counted over /api/chat calls:

* ``{"chat_call": n, "mode": "drop"}`` — the n-th chat request is cut off: the
  connection closes with no response (a server dying mid-request, once);
* ``{"chat_call": n, "mode": "runner_error"}`` — HTTP 500 "llama runner process
  no longer running: -1" (Ollama's response when its runner is killed);
* ``{"chat_call": n, "mode": "exit"}`` — the server process exits mid-request
  and stays down (a permanent failure).

Runner-loss faults for the watchdog (RUNBOOK A.8, 24 Oct):

* ``{"chat_call": n, "mode": "sigterm"}`` — the server sends itself SIGTERM
  mid-request (the 14 Oct incident: the model runner received SIGTERM);
* ``{"chat_call": n, "mode": "freeze"}`` — every later request, including
  ``/api/version``, hangs (an unresponsive server);
* ``{"chat_call": n, "mode": "unload"}`` — the model is gone: ``/api/ps`` lists
  no model and chat calls answer the runner error (a lost model runner).

Each fault fires once per DRYRUN root (marker ``fault_<n>_<mode>.fired``), so a
server restarted by the watchdog, whose chat counter starts again at 1, does not
fire it again.  Each request is also printed as a ``[GIN]``-style line on stdout
(the instance's serve log), like the real server's request log.

AI-assisted (Claude).  ENGINEERING_ONLY / DRYRUN.
"""
import json
import os
import platform
import re
import signal
import socket
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MODEL = 'qwen2.5-coder:7b'
DIGEST = 'dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364'
LOCK = threading.Lock()
STATE = {'chat_calls': 0, 'frozen': False, 'unloaded': False}
FAULTS = {int(f['chat_call']): f['mode'] for f in json.loads(os.environ.get('C3_FAKE_FAULTS') or '[]')}
ROOT = Path(os.environ.get('R1_FAKE_OLLAMA_ROOT', '/nonexistent'))
INACTIVE_SENT = set()


def log(entry):
    with LOCK, (ROOT / 'fake_calls.jsonl').open('a') as f:
        f.write(json.dumps({'label': 'DRYRUN', 'pid': os.getpid(), **entry}) + '\n')


def request_line(method, path, status, extra=''):
    stamp = datetime.now(timezone.utc).strftime('%Y/%m/%d - %H:%M:%S')
    print(f'[GIN] {stamp} | {status} | DRYRUN | 127.0.0.1 | {method} "{path}" {extra}'.rstrip(), flush=True)


def fire_once(n, mode):
    """True the first time fault (n, mode) fires under this DRYRUN root."""
    marker = ROOT / f'fault_{n}_{mode}.fired'
    try:
        with marker.open('x') as f:
            f.write(json.dumps({'pid': os.getpid(), 'chat_call': n, 'mode': mode}) + '\n')
        return True
    except FileExistsError:
        return False


def hold_if_frozen():
    while STATE['frozen']:
        time.sleep(0.5)


def proposal_for(prompt, seed):
    trial = int(re.search(r'Budget index \(trial number\): (\d+)', prompt).group(1))
    if 'Node: openml_' in prompt:
        inactive = trial == 3 and seed not in INACTIVE_SENT and re.search(r'^  max_depth = ', prompt, re.M) is None
        if inactive:
            INACTIVE_SENT.add(seed)
        key = 'max_depth' if inactive else 'C'
        found = re.search(r'^  C = (.+)$', prompt, re.M)
        old = found.group(1) if found else '1.0'
        value = str(round(0.001 * 2 ** (trial - 1) + (seed or 0) % 7 * 1e-4, 6)) if key == 'C' else '7'
    else:
        key = 'MAX_ITER'
        found = re.search(r'^  MAX_ITER = (.+)$', prompt, re.M)
        old = found.group(1) if found else '200'
        value = str(16 + trial * 4 + (seed or 0) % 3)
    return {'summary': f'DRYRUN fixture proposal at trial {trial}', 'rationale': 'DRYRUN HTTP fixture; no inference',
            'param': key, 'old_value': old, 'new_value': value,
            'objective': f'Change {key} from {old} to {value}'}


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):
        pass

    def reply(self, value, status=200, ndjson=False):
        data = (json.dumps(value) + '\n').encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/x-ndjson' if ndjson else 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        hold_if_frozen()
        model = {'name': MODEL, 'model': MODEL, 'digest': DIGEST, 'size': 5560907776,
                 'size_vram': 5560907776, 'expires_at': '2099-01-01T00:00:00Z'}
        log({'path': self.path})
        if self.path == '/api/version':
            self.reply({'version': 'DRYRUN'})
        elif self.path == '/api/ps' and STATE['unloaded']:
            self.reply({'models': []})
        else:
            self.reply({'models': [model]})

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])) or b'{}')
        seed = body.get('options', {}).get('seed')
        if self.path != '/api/chat':
            log({'path': self.path, 'seed': seed})
            self.reply({'model': MODEL, 'response': 'OK', 'done': True, 'status': 'success'})
            return
        hold_if_frozen()
        with LOCK:
            STATE['chat_calls'] += 1
            n = STATE['chat_calls']
        fault = FAULTS.get(n)
        if fault is not None and not fire_once(n, fault):
            fault = None
        log({'path': self.path, 'seed': seed, 'chat_call': n, 'fault': fault})
        request_line('POST', self.path, 'fault=' + fault if fault else 200, f'chat_call={n}')
        if fault == 'sigterm':
            log({'event': 'fake server sends itself SIGTERM (runner loss)', 'chat_call': n})
            os.kill(os.getpid(), signal.SIGTERM)
            time.sleep(5)
            return
        if fault == 'freeze':
            log({'event': 'fake server freezes (unresponsive)', 'chat_call': n})
            STATE['frozen'] = True
            hold_if_frozen()
            return
        if fault == 'unload':
            log({'event': 'fake model runner lost (model unloaded)', 'chat_call': n})
            STATE['unloaded'] = True
        if STATE['unloaded']:
            self.reply({'error': 'llama runner process no longer running: -1 '}, status=500)
            return
        if fault == 'drop':
            self.connection.shutdown(socket.SHUT_RDWR)
            self.close_connection = True
            return
        if fault == 'runner_error':
            self.reply({'error': 'llama runner process no longer running: -1 '}, status=500)
            return
        if fault == 'exit':
            log({'event': 'fake server exiting (permanent failure)', 'chat_call': n})
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
            finally:
                os._exit(17)
        prompt = '\n'.join(m.get('content', '') for m in body.get('messages', []))
        content = json.dumps(proposal_for(prompt, seed))
        self.reply({'model': MODEL, 'created_at': '2026-10-19T00:00:00Z',
                    'message': {'role': 'assistant', 'content': content}, 'done': True, 'done_reason': 'stop',
                    'prompt_eval_count': 10, 'eval_count': 10, 'total_duration': 1000000}, ndjson=True)


def main():
    if platform.node().split('.')[0] == 'ucrtasl':
        raise SystemExit('STOP: fake Ollama is forbidden on Ada')
    if not (ROOT / '.dryrun').is_file():
        raise SystemExit('STOP: fake Ollama requires a marked DRYRUN directory (R1_FAKE_OLLAMA_ROOT)')
    command = sys.argv[1] if len(sys.argv) > 1 else 'serve'
    if command == 'pull':
        log({'event': 'pull', 'model': sys.argv[2:]})
        return
    if command != 'serve':
        raise SystemExit(f'fake ollama: unsupported command {command!r}')
    host = os.environ.get('OLLAMA_HOST', '127.0.0.1:11434')
    port = int(host.rsplit(':', 1)[1])
    log({'event': 'serve', 'port': port, 'models': os.environ.get('OLLAMA_MODELS')})
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()


if __name__ == '__main__':
    main()
