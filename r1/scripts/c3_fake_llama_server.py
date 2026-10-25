"""HTTP-only fake ``llama-server`` for the C3 sweep desktop DRYRUN and tests; no inference (RUNBOOK A.10).

Invoked like the real binary: ``--version`` prints a ``version: <n> (<commit>)``
line on stderr; otherwise ``-m <gguf> --host 127.0.0.1 --port <p> -ngl <n>
-c <ctx> --alias <alias> -np 1``.  The GGUF path must exist (any file: the
runner pins its sha256).  Refuses on Ada and outside a marked DRYRUN
directory (``$R1_FAKE_OLLAMA_ROOT/.dryrun``, the variable the launcher already
exports in DRYRUN).  Every request is logged to ``fake_calls.jsonl`` there.

Endpoints, as llama-server: ``/health`` (503 "Loading model" for
``$C3_FAKE_LLAMA_LOAD_SECONDS``, default 0.3 s, then 200 ``{"status": "ok"}``),
``/v1/models`` (the alias), ``/props`` (``model_path``, slots, context), and
``/v1/chat/completions`` (OpenAI-compatible; the request's top-level ``seed``
is logged).  Only ``/v1/...`` serves chat, so a client without the ``/v1``
prefix fails here.

Load log on stdout, in llama.cpp's wording: ``load_tensors: offloaded k/29
layers to GPU`` with k = min(-ngl, 29) and a ``CUDA0 model buffer size`` line.
``$C3_FAKE_LLAMA_OFFLOAD``: ``cpu`` prints llama.cpp's no-GPU warning and
``offloaded 0/29``; an integer k prints ``offloaded k/29`` (partial offload).
Each request is printed as ``srv  log_server_r: request: POST <path> 127.0.0.1
<status>`` (llama-server's request log line), with ``fault=<mode>`` and the
chat-call number appended.

Fault injection: ``$C3_FAKE_FAULTS`` as for the fake Ollama
(``r1/scripts/c3_fake_ollama.py``), counted over chat calls and fired once
per DRYRUN root: ``drop``, ``exit``, ``runner_error`` (HTTP 500), ``sigterm``,
``freeze``, ``unload`` (``/v1/models`` lists no model; chats answer 500).

AI-assisted (Claude).  ENGINEERING_ONLY / DRYRUN.
"""
import json
import os
import platform
import signal
import socket
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c3_fake_ollama as common  # noqa: E402  (fault markers, call log, DRYRUN proposals)

VERSION = 'version: 0 (DRYRUN)'
N_LAYERS = 29
ARGS: dict = {}
STARTED = time.monotonic()


def log(entry):
    common.log({'server': 'llama-server', **entry})


def request_line(method, path, status, extra=''):
    print(f'srv  log_server_r: request: {method} {path} 127.0.0.1 {status} {extra}'.rstrip(), flush=True)


def parse(argv):
    args = {'-m': None, '--host': '127.0.0.1', '--port': '8080', '-ngl': '0', '-c': '4096', '--alias': None, '-np': '1'}
    it = iter(argv)
    for item in it:
        if item in args:
            args[item] = next(it)
        else:
            raise SystemExit(f'fake llama-server: unsupported argument {item!r}')
    return args


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):
        pass

    def reply(self, value, status=200):
        data = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        common.hold_if_frozen()
        log({'path': self.path})
        loading = time.monotonic() - STARTED < float(os.environ.get('C3_FAKE_LLAMA_LOAD_SECONDS', '0.3'))
        if self.path == '/health':
            if loading:
                self.reply({'error': {'code': 503, 'message': 'Loading model', 'type': 'unavailable_error'}}, 503)
            else:
                self.reply({'status': 'ok'})
        elif self.path in ('/v1/models', '/models'):
            data = [] if common.STATE['unloaded'] else [
                {'id': ARGS['--alias'] or ARGS['-m'], 'object': 'model', 'created': 0, 'owned_by': 'llamacpp',
                 'meta': {'n_ctx_train': 32768, 'size': 4683073504, 'DRYRUN': True}}]
            self.reply({'object': 'list', 'data': data})
        elif self.path == '/props':
            self.reply({'model_path': ARGS['-m'], 'total_slots': int(ARGS['-np']), 'build_info': VERSION,
                        'default_generation_settings': {'n_ctx': int(ARGS['-c'])}})
        else:
            self.reply({'error': {'code': 404, 'message': 'File Not Found', 'type': 'not_found_error'}}, 404)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])) or b'{}')
        seed = body.get('seed')
        if self.path != '/v1/chat/completions':
            log({'path': self.path, 'seed': seed})
            request_line('POST', self.path, 404)
            self.reply({'error': {'code': 404, 'message': 'File Not Found', 'type': 'not_found_error'}}, 404)
            return
        common.hold_if_frozen()
        if body.get('max_tokens') == 1 and 'Budget index' not in json.dumps(body.get('messages')):
            log({'path': self.path, 'seed': seed, 'probe': True})  # the runner's one-token load probe
            request_line('POST', self.path, 200, 'probe')
            self.reply(self.completion(body, 'OK'))
            return
        with common.LOCK:
            common.STATE['chat_calls'] += 1
            n = common.STATE['chat_calls']
        fault = common.FAULTS.get(n)
        if fault is not None and not common.fire_once(n, fault):
            fault = None
        log({'path': self.path, 'seed': seed, 'chat_call': n, 'fault': fault, 'model': body.get('model')})
        request_line('POST', self.path, 'fault=' + fault if fault else 200, f'chat_call={n}')
        if fault == 'sigterm':
            log({'event': 'fake llama-server sends itself SIGTERM (runner loss)', 'chat_call': n})
            os.kill(os.getpid(), signal.SIGTERM)
            time.sleep(5)
            return
        if fault == 'freeze':
            log({'event': 'fake llama-server freezes (unresponsive)', 'chat_call': n})
            common.STATE['frozen'] = True
            common.hold_if_frozen()
            return
        if fault == 'unload':
            log({'event': 'fake llama-server lost its model', 'chat_call': n})
            common.STATE['unloaded'] = True
        if common.STATE['unloaded'] or fault == 'runner_error':
            self.reply({'error': {'code': 500, 'message': 'DRYRUN: model unavailable', 'type': 'server_error'}}, 500)
            return
        if fault == 'drop':
            self.connection.shutdown(socket.SHUT_RDWR)
            self.close_connection = True
            return
        if fault == 'exit':
            log({'event': 'fake llama-server exiting (permanent failure)', 'chat_call': n})
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
            finally:
                os._exit(17)
        prompt = '\n'.join(str(m.get('content', '')) for m in body.get('messages', []))
        self.reply(self.completion(body, json.dumps(common.proposal_for(prompt, seed))))

    def completion(self, body, content):
        return {'id': 'chatcmpl-DRYRUN', 'object': 'chat.completion', 'created': 0,
                'model': body.get('model'), 'system_fingerprint': 'b0-DRYRUN',
                'choices': [{'index': 0, 'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': content}}],
                'usage': {'prompt_tokens': 10, 'completion_tokens': 10, 'total_tokens': 20}}


def load_log():
    ngl = int(ARGS['-ngl'])
    mode = os.environ.get('C3_FAKE_LLAMA_OFFLOAD', '')
    k = min(max(ngl, 0), N_LAYERS)
    if mode == 'cpu':
        print('warning: no usable GPU found, --gpu-layers option will be ignored', flush=True)
        k = 0
    elif mode.isdigit():
        k = min(int(mode), N_LAYERS)
    print(f'llama_model_loader: loaded meta data from {ARGS["-m"]} (DRYRUN fixture; no tensors)', flush=True)
    print(f'load_tensors: offloading {max(k - 1, 0)} repeating layers to GPU', flush=True)
    print(f'load_tensors: offloaded {k}/{N_LAYERS} layers to GPU', flush=True)
    if k:
        print('load_tensors:        CUDA0 model buffer size =  4168.09 MiB', flush=True)
        print('llama_kv_cache_unified:      CUDA0 KV buffer size =   448.00 MiB', flush=True)
    print('load_tensors:   CPU_Mapped model buffer size =   292.36 MiB', flush=True)


def main():
    global ARGS, STARTED
    argv = sys.argv[1:]
    if argv == ['--version']:
        print(VERSION, file=sys.stderr)
        print('built with DRYRUN fixture (no inference) for any', file=sys.stderr)
        return
    if platform.node().split('.')[0] == 'ucrtasl':
        raise SystemExit('STOP: fake llama-server is forbidden on Ada')
    if not (common.ROOT / '.dryrun').is_file():
        raise SystemExit('STOP: fake llama-server requires a marked DRYRUN directory (R1_FAKE_OLLAMA_ROOT)')
    ARGS = parse(argv)
    if not ARGS['-m'] or not Path(ARGS['-m']).is_file():
        raise SystemExit(f'fake llama-server: model file not found: {ARGS["-m"]}')
    port = int(ARGS['--port'])
    log({'event': 'serve', 'port': port, 'model': ARGS['-m'], 'alias': ARGS['--alias'], 'ngl': ARGS['-ngl'],
         'env_llama_arg': sorted(k for k in os.environ if k.startswith('LLAMA_ARG_'))})
    load_log()
    server = ThreadingHTTPServer((ARGS['--host'], port), Handler)
    STARTED = time.monotonic()
    print(f'main: server is listening on http://{ARGS["--host"]}:{port} - starting the main loop', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
