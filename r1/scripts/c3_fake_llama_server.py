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
``$C3_FAKE_LLAMA_OFFLOAD``: ``line`` (default) as just described; ``silent``
prints only what llama.cpp v0.7.0 (commit 620d222) printed on deepthought at
default verbosity (no offload and no buffer line; review of batch B, 25 Oct);
``cpu`` prints llama.cpp's no-GPU warning and ``offloaded 0/29``; an integer k
prints ``offloaded k/29`` (partial offload).

Simulated GPU memory (offload route (ii)): unless ``cpu``, the server writes
``$R1_FAKE_OLLAMA_ROOT/gpu_apps/<pid>.csv`` = ``<pid>, <CUDA_VISIBLE_DEVICES or
GPU-DRYRUN>, <MiB>`` with ``$C3_FAKE_LLAMA_GPU_MIB`` (default 5560; 0 = none;
300 with ``-ngl 0``).  Run as ``run_name="fake_nvidia_smi"`` this file is a fake
``nvidia-smi`` whose ``--query-compute-apps`` lists those rows for live pids.
Completions carry llama-server's ``timings`` (``predicted_per_second`` =
``$C3_FAKE_LLAMA_TPS_GPU`` (40) when layers are on the GPU, else
``$C3_FAKE_LLAMA_TPS_CPU`` (8)) for the probe's CPU control run.
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
import threading
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
        if item == '--jinja':
            args[item] = True
        elif item in args or item in ('--cache-type-k', '--cache-type-v', '--chat-template-kwargs', '--reasoning-budget'):
            args[item] = next(it)
        elif item in ('-lv', '--verbosity', '--log-verbosity'):
            # Exam evidence plumbing: real llama.cpp accepts the verbosity flag;
            # the fake accepts and ignores it so the exam argv stays truthful.
            args[item] = next(it)
        elif item in ('-v', '--verbose', '--log-verbose'):
            args[item] = True
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
        if self.path == '/tokenize':
            self.reply({'tokens': [1, 2]})
            return
        if self.path == '/completion':
            if len(body['prompt']) >= int(ARGS['-c']):
                self.reply({'error': 'prompt must leave a context slot'}, 400)
                return
            self.reply({'content': 'x', 'tokens_evaluated': len(body['prompt']), 'tokens_predicted': max(1, body.get('n_predict', 1))})
            return
        if self.path == '/apply-template':
            self.reply({'prompt': ''.join(f"{m['role']}: {m['content']}\n" for m in body['messages']) + 'assistant: '})
            return
        if self.path != '/v1/chat/completions':
            log({'path': self.path, 'seed': seed})
            request_line('POST', self.path, 404)
            self.reply({'error': {'code': 404, 'message': 'File Not Found', 'type': 'not_found_error'}}, 404)
            return
        common.hold_if_frozen()
        text = '\n'.join(str(m.get('content', '')) for m in body.get('messages', []))
        side = side_answer(text)
        if side is not None:  # Track H dry run: an A4 typed question or an LLM self-control query
            log({'path': self.path, 'seed': seed, 'side_query': side[0]})
            request_line('POST', self.path, 200, f'side_query={side[0]}')
            self.reply(self.completion(body, side[1]))
            return
        if 'Budget index' not in json.dumps(body.get('messages')):
            log({'path': self.path, 'seed': seed, 'probe': True})  # a load probe or the probe's throughput run
            request_line('POST', self.path, 200, 'probe')
            self.reply(self.completion(body, 'OK'))
            return
        with common.LOCK:
            common.STATE['chat_calls'] += 1
            n = common.STATE['chat_calls']
        fault = common.FAULTS.get(n)
        if fault is not None and not common.fire_once(n, fault):
            fault = None
        log({'path': self.path, 'seed': seed, 'chat_call': n, 'fault': fault, 'model': body.get('model'),
             **({'response_format': body['response_format']} if 'response_format' in body else {})})
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
        if os.environ.get('EXAM_FAKE_MALFORMED') == '1':
            content='malformed DRYRUN reply'
        elif prompt.startswith('You proposed the edit below.'):
            content=json.dumps({'p_no_effect':0.2,'p_positive':0.7,'size':'small'})
        else:
            content=json.dumps(common.proposal_for(prompt,seed))
        self.reply(self.completion(body, content))

    def completion(self, body, content):
        n = int(body.get('max_tokens') or 10)
        tps = float(os.environ.get('C3_FAKE_LLAMA_TPS_GPU', '40') if on_gpu() else
                    os.environ.get('C3_FAKE_LLAMA_TPS_CPU', '8'))
        budget=int(body.get('reasoning_budget_tokens',body.get('thinking_budget_tokens',ARGS.get('--reasoning-budget') or 0)))
        kwargs=json.loads(ARGS.get('--chat-template-kwargs') or '{}');kwargs.update(body.get('chat_template_kwargs') or {})
        thinking=bool(kwargs.get('enable_thinking',budget>0)) and budget>0
        return {'id': 'chatcmpl-DRYRUN', 'object': 'chat.completion', 'created': 0,
                'model': body.get('model'), 'system_fingerprint': 'b0-DRYRUN',
                'choices': [{'index': 0, 'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': content,
                    **({'reasoning_content': 'DRYRUN reasoning fixture'} if thinking else {})}}],
                'usage': {'prompt_tokens': 10, 'completion_tokens': n, 'total_tokens': 10 + n,
                    **({'completion_tokens_details': {'reasoning_tokens': 1}} if thinking else {})},
                'timings': {'predicted_n': n, 'predicted_ms': 1000.0 * n / tps, 'predicted_per_second': tps}}


def side_answer(text):
    """Track H dry run (25 Oct): deterministic replies to the controller's side queries, keyed by the prompt.

    An A4 typed question (``"p_no_effect"`` in the prompt) gets typed answers; an
    LLM self-control query (``r1.llm_control.build_side_prompt``) gets ``continue``,
    or ``skip`` at E1 for about one prompt in three.  Anything else returns None
    (handled as before).  No inference.
    """
    import hashlib
    h = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
    if '"p_no_effect"' in text:
        sizes = ('tiny', 'small', 'medium', 'large')
        return 'a4', json.dumps({'p_no_effect': round((h % 5) / 20, 3), 'p_positive': round(0.2 + (h % 7) / 10, 3),
                                 'size': sizes[h % 4]})
    if 'You are advising the control plane' in text:
        skip = 'Decision epoch: E1' in text and '  skip:' in text and h % 3 == 0
        return 'self_control', json.dumps({'action': 'skip' if skip else 'continue', 'scores': {}})
    return None


def offload_mode():
    return os.environ.get('C3_FAKE_LLAMA_OFFLOAD', '') or 'line'


def on_gpu():
    return int(ARGS['-ngl']) > 0 and offload_mode() != 'cpu' and offload_mode() != '0' 


def load_log():
    ngl = int(ARGS['-ngl'])
    mode = offload_mode()
    k = min(max(ngl, 0), N_LAYERS)
    if mode == 'silent':  # llama.cpp v0.7.0 at default verbosity (deepthought, 25 Oct)
        print('common_params_print_info: verbosity = 3 (adjust with the `-lv N` CLI arg)', flush=True)
        print(f'load_model: initializing, n_slots = {ARGS["-np"]}, n_ctx_slot = {ARGS["-c"]}, kv_unified = \'true\'',
              flush=True)
        print('llama_server: model loaded', flush=True)
        return
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
    if os.environ.get('C3_FAKE_EXIT_IF_ORPHANED')=='1':
        parent=os.getppid()
        if parent==1: raise SystemExit('STOP: fake server has no original parent')
        def parent_watch():
            while os.getppid()==parent:
                time.sleep(.05)
            try: log({'event':'parent_lost_self_exit'})
            except OSError: pass
            os._exit(0)
        threading.Thread(target=parent_watch,daemon=True).start()
    ARGS = parse(argv)
    if not ARGS['-m'] or not Path(ARGS['-m']).is_file():
        raise SystemExit(f'fake llama-server: model file not found: {ARGS["-m"]}')
    port = int(ARGS['--port'])
    log({'event': 'serve', 'port': port, 'model': ARGS['-m'], 'alias': ARGS['--alias'], 'ngl': ARGS['-ngl'],
         'env_llama_arg': sorted(k for k in os.environ if k.startswith('LLAMA_ARG_'))})
    load_log()
    simulate_gpu_memory()
    server = ThreadingHTTPServer((ARGS['--host'], port), Handler)
    STARTED = time.monotonic()
    print(f'main: server is listening on http://{ARGS["--host"]}:{port} - starting the main loop', flush=True)
    server.serve_forever()


def simulate_gpu_memory():
    """The fake's GPU footprint, for the fake nvidia-smi below (offload route (ii))."""
    if offload_mode() == 'cpu':
        return
    mib = int(os.environ.get('C3_FAKE_LLAMA_GPU_MIB', '5560')) if int(ARGS['-ngl']) > 0 else 300
    if mib <= 0:
        return
    apps = common.ROOT / 'gpu_apps'
    apps.mkdir(exist_ok=True)
    uuid = os.environ.get('CUDA_VISIBLE_DEVICES') or 'GPU-DRYRUN'
    (apps / f'{os.getpid()}.csv').write_text(f'{os.getpid()}, {uuid}, {mib}\n')


def fake_nvidia_smi(argv):
    """``nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory`` over the live fake servers; else a card."""
    joined = ' '.join(argv)
    if '--query-compute-apps' in joined:
        for path in sorted((common.ROOT / 'gpu_apps').glob('*.csv')):
            pid = int(path.stem)
            try:
                os.kill(pid, 0)
                # The synthetic GPU app list is also used by desktop tests on
                # macOS, which has no procfs. On Linux keep the zombie check;
                # on other systems kill(0) is the conservative liveness proxy.
                if sys.platform.startswith('linux'):
                    stat = Path(f'/proc/{pid}/stat').read_text()
                    if stat.rsplit(')', 1)[1].split()[0] == 'Z':
                        continue
            except (OSError, IndexError):
                continue
            print(path.read_text().strip())
        return
    if '--query-gpu' in joined:
        print('0, GPU-DRYRUN, DRYRUN shared card, 40000')
        return
    print('DRYRUN GPU census')


if __name__ == '__main__':
    main()
elif __name__ == 'fake_nvidia_smi':
    fake_nvidia_smi(sys.argv[1:])
